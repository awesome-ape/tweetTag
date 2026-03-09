import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import ReturnDocument

from backend.app.db.database import escalation_collection
from backend.app.schemas.tweet_scheme import TweetinDB, taggSchema
from backend.app.services.tweets.tagger import submit_tagged_tweet, release_lock

env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"

if env_path.exists():
    # Local: Load the file from your 4-level deep path
    load_dotenv(dotenv_path=env_path)
else:
    # AWS: The file is missing, so use the variables in the Console
    load_dotenv()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _timeout_seconds() -> int:
    return int(os.getenv("TIMEOUT_LIMIT", "300"))


async def get_escalated_tweets(limit: int = 200) -> List[TweetinDB]:
    cursor = (
        escalation_collection.find({})
        .sort([("queued_at", -1), ("_id", -1)])
        .limit(limit)
    )

    tweets: List[TweetinDB] = []
    async for doc in cursor:
        t = TweetinDB.from_mongo(doc)
        if t:
            tweets.append(t)
    return tweets


async def claim_escalated_tweet(tweet_id: str, user_id: str) -> Optional[TweetinDB]:
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
            {"status": "tagging", "locked_by": str(user_id)},
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

    doc = await escalation_collection.find_one_and_update(
        query,
        update,
        return_document=ReturnDocument.AFTER,
    )

    return TweetinDB.from_mongo(doc) if doc else None


async def release_escalated_lock(tweet_id: str, user_id: str) -> bool:
    return await release_lock(tweet_id, user_id, escalation_collection)


async def submit_escalated_tagged_tweet(payload: taggSchema) -> bool:
    # tagged_at is added automatically by taggSchema / submit_tagged_tweet
    return await submit_tagged_tweet(payload, escalation_collection)