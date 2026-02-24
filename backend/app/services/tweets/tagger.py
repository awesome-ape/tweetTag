import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import ReturnDocument

from backend.app.db.database import (
    escalation_collection,
    processed_collection,
    working_collection,
)
from backend.app.schemas.tweet_scheme import TweetinDB, taggSchema, esclateSchema

base_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _timeout_seconds() -> int:
    return int(os.getenv("TIMEOUT_LIMIT", "300"))


def _expiry_time() -> datetime:
    return _now_utc() - timedelta(seconds=_timeout_seconds())


async def claim_tweet(collection, user_id: str) -> Optional[TweetinDB]:
    """
    Claim ONE tweet for tagging.
    We only allow claiming tweets that are:
    - pending / status missing / status None
    - OR tagging but stale/invalid lock
    """
    expiry_time = _expiry_time()

    query = {
        "$or": [
            {"status": {"$exists": False}},
            {"status": None},
            {"status": "pending"},

            # stale/invalid locks
            {"status": "tagging", "locked_at": {"$lt": expiry_time}},
            {"status": "tagging", "locked_at": {"$exists": False}},
            {"status": "tagging", "locked_at": None},
        ]
    }

    update = {
        "$set": {
            "status": "tagging",
            "locked_at": _now_utc(),
            "locked_by": str(user_id),
        }
    }

    tweet_data = await collection.find_one_and_update(
        query,
        update,
        return_document=ReturnDocument.AFTER,
    )

    if not tweet_data:
        return None

    return TweetinDB.from_mongo(tweet_data)


async def submit_tagged_tweet(payload: taggSchema, collection) -> bool:
    try:
        oid = ObjectId(str(payload.tweet_id))
    except Exception:
        raise ValueError("Submission failed: invalid tweet id.")

    # Verify ownership + lock validity (locked_at must match!)
    query = {
        "_id": oid,
        "status": "tagging",
        "locked_at": payload.locked_at,
        "locked_by": str(payload.tagged_by),
    }

    update = {
        "$set": {
            "status": "tagged",
            "is_dangerous": payload.is_dangerous,
            "category": payload.category,
            "tagged_by": payload.tagged_by,
        },
        "$unset": {"locked_at": "", "locked_by": ""},
    }

    tweet = await collection.find_one_and_update(
        query,
        update,
        return_document=ReturnDocument.AFTER,
    )

    if not tweet:
        raise ValueError("Submission failed: lock invalid / expired / not owned by user.")

    # Move to processed if coming from working (upsert prevents DuplicateKey)
    if collection != processed_collection:
        await processed_collection.replace_one({"_id": tweet["_id"]}, tweet, upsert=True)
        await collection.delete_one({"_id": tweet["_id"]})

    return True


async def release_lock(tweet_id: str, user_id: str, collection) -> bool:
    """
    Idempotent unlock.

    - If the tweet is locked by THIS user, we remove the lock.
    - If it's not locked / not owned / already moved / not found: we return True
      (so frontend doesn't get stuck and locks won't accumulate).

    We ONLY change status back to default if current status is "tagging".
    Otherwise, we just unset the lock fields safely.
    """
    try:
        oid = ObjectId(str(tweet_id))
    except Exception:
        # invalid id -> treat as "nothing to release" for UX
        return True

    default_status = "tagged" if collection == processed_collection else "pending"

    doc = await collection.find_one(
        {"_id": oid},
        {"status": 1, "locked_by": 1, "locked_at": 1},
    )

    # Already gone -> nothing to release
    if not doc:
        return True

    # Locked by someone else or not locked -> don't fail UX
    if doc.get("locked_by") != str(user_id):
        return True

    # If it's tagging, revert status and clear lock
    if doc.get("status") == "tagging":
        await collection.update_one(
            {"_id": oid, "locked_by": str(user_id)},
            {
                "$set": {"status": default_status},
                "$unset": {"locked_at": "", "locked_by": ""},
            },
        )
        return True

    # Otherwise just clear lock fields (safe)
    await collection.update_one(
        {"_id": oid, "locked_by": str(user_id)},
        {"$unset": {"locked_at": "", "locked_by": ""}},
    )
    return True


async def escalate_tweet(payload: esclateSchema, user_id: str) -> bool:
    """
    Escalation requires a valid lock (locked_at must match).
    """
    try:
        oid = ObjectId(str(payload.tweet_id))
    except Exception:
        raise ValueError("Escalation failed: invalid tweet id.")

    if payload.locked_at is None:
        raise ValueError("Escalation failed: missing locked_at.")

    query = {
        "_id": oid,
        "status": "tagging",
        "locked_at": payload.locked_at,
        "locked_by": str(user_id),
    }

    tweet = await working_collection.find_one(query)
    if not tweet:
        raise ValueError("Escalation failed: lock invalid / expired / not owned by user.")

    tweet["status"] = "pending"
    tweet.pop("locked_at", None)
    tweet.pop("locked_by", None)
    tweet["queued_at"] = _now_utc()

    await escalation_collection.insert_one(tweet)
    await working_collection.delete_one({"_id": tweet["_id"]})
    return True


async def release_stale_locks(collection) -> None:
    """
    Background job to release stale locks.
    """
    stat = "tagged" if collection == processed_collection else "pending"

    while True:
        cutoff_time = _expiry_time()

        result = await collection.update_many(
            {
                "status": "tagging",
                "$or": [
                    {"locked_at": {"$lt": cutoff_time}},
                    {"locked_at": None},
                    {"locked_at": {"$exists": False}},
                ],
            },
            {
                "$set": {"status": stat},
                "$unset": {"locked_at": "", "locked_by": ""},
            },
        )

        if result.modified_count > 0:
            print(f"✅ Released {result.modified_count} stale tweet locks.")

        await asyncio.sleep(60)


async def get_my_tagged_tweets(user_id: str, limit: int = 200) -> List[TweetinDB]:
    cursor = (
        processed_collection.find({"tagged_by": str(user_id)})
        .sort([("_id", -1)])
        .limit(limit)
    )

    tweets: List[TweetinDB] = []
    async for doc in cursor:
        t = TweetinDB.from_mongo(doc)
        if t:
            tweets.append(t)

    return tweets


async def claim_processed_tweet(tweet_id: str, user_id: str) -> Optional[TweetinDB]:
    try:
        oid = ObjectId(str(tweet_id))
    except Exception:
        return None

    expiry_time = _expiry_time()

    query = {
        "_id": oid,
        "$or": [
            {"status": {"$exists": False}},
            {"status": None},
            {"status": "pending"},
            {"status": "tagged"},

            # reclaim by same admin
            {"status": "tagging", "locked_by": str(user_id)},

            # stale/invalid locks
            {"status": "tagging", "locked_at": {"$lt": expiry_time}},
            {"status": "tagging", "locked_at": {"$exists": False}},
            {"status": "tagging", "locked_at": None},
        ],
    }

    update = {
        "$set": {
            "status": "tagging",
            "locked_at": _now_utc(),
            "locked_by": str(user_id),
        }
    }

    doc = await processed_collection.find_one_and_update(
        query,
        update,
        return_document=ReturnDocument.AFTER,
    )
    return TweetinDB.from_mongo(doc) if doc else None