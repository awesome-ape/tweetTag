import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import ReturnDocument
from typing import List
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


async def claim_tweet(collection, user_id: str) -> Optional[TweetinDB]:
    expiry_time = _now_utc() - timedelta(seconds=_timeout_seconds())

    query = {
        "$or": [
            {"status": {"$ne": "tagging"}},
            {"status": {"$exists": False}},
            {"status": None},
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

    # 1. Verify ownership and lock status
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

    # Execute the update in the source collection
    tweet = await collection.find_one_and_update(
        query,
        update,
        return_document=ReturnDocument.AFTER,
    )

    if not tweet:
        raise ValueError(
            "Submission failed: lock invalid / expired / not owned by user."
        )

    # 2. Handle the "Move or Update" logic
    # If we are NOT in processed yet, move it there and delete the original
    if collection != processed_collection:
        # replace_one with upsert=True prevents DuplicateKey errors if it exists
        await processed_collection.replace_one(
            {"_id": tweet["_id"]}, tweet, upsert=True
        )
        await collection.delete_one({"_id": tweet["_id"]})

    # If we ARE already in processed_collection, find_one_and_update
    # already saved the changes. We are done.

    return True


async def release_lock(tweet_id: str, user_id: str, collection) -> bool:
    if collection == processed_collection:
        stat = "tagged"
    else:
        stat = "pending"
    try:
        oid = ObjectId(str(tweet_id))
    except Exception:
        return False

    res = await collection.update_one(
        {"_id": oid, "status": "tagging", "locked_by": str(user_id)},
        {"$set": {"status": stat}, "$unset": {"locked_at": "", "locked_by": ""}},
    )
    return res.modified_count == 1


async def escalate_tweet(payload: esclateSchema, user_id: str) -> bool:
    """
    payload has: tweet_id, locked_at (per your schema)
    user_id comes from current_user (server-side), not from payload.
    """
    try:
        oid = ObjectId(str(payload.tweet_id))
    except Exception:
        raise ValueError("Escalation failed: invalid tweet id.")

    query = {
        "_id": oid,
        "status": "tagging",
        "locked_at": payload.locked_at,
        "locked_by": str(user_id),
    }

    tweet = await working_collection.find_one(query)
    if not tweet:
        raise ValueError(
            "Escalation failed: lock invalid / expired / not owned by user."
        )

    tweet["status"] = "pending"
    tweet.pop("locked_at", None)
    tweet.pop("locked_by", None)

    # Optional but recommended for sorting in admin queue:
    tweet["queued_at"] = _now_utc()

    await escalation_collection.insert_one(tweet)
    await working_collection.delete_one({"_id": tweet["_id"]})
    return True


async def release_stale_locks(collection) -> None:
    timeout_limit = _timeout_seconds()
    stat = "pending"
    if collection == processed_collection:
        stat = "tagged"

    while True:
        cutoff_time = _now_utc() - timedelta(seconds=timeout_limit)

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


from typing import List


async def get_my_tagged_tweets(user_id: str, limit: int = 200) -> List[TweetinDB]:
    """
    Returns tweets from processed_collection that were tagged
    by the currently authenticated user.
    """
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

    expiry_time = _now_utc() - timedelta(seconds=_timeout_seconds())

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
