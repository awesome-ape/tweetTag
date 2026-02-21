import asyncio
from unittest import result
from backend.app.db.database import (
    backup_collection,
    escalation_collection,
    working_collection,
    processed_collection,
)
from backend.app.schemas.tweet_scheme import (
    TweetinDB,
    TweetSchema,
    taggSchema,
    esclateSchema,
)
from typing import List
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from pathlib import Path
from pymongo import ReturnDocument
from bson import ObjectId

base_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")


async def claim_tweet(collection) -> TweetinDB | None:
    timeout_limit = int(
        os.getenv("TIMEOUT_LIMIT", "300")
    )  # default to 5 minutes if not set
    expiry_time = datetime.now(timezone.utc) - timedelta(seconds=timeout_limit)

    query = {
        "$or": [
            {"status": "pending"},
            {"status": "tagging", "locked_at": {"$lt": expiry_time}},
        ]
    }

    update = {"$set": {"status": "tagging", "locked_at": datetime.now(timezone.utc)}}

    tweet_data = await collection.find_one_and_update(
        query, update, return_document=ReturnDocument.AFTER
    )
    if not tweet_data:
        return None

    return TweetinDB.from_mongo(tweet_data)


async def submit_tagged_tweet(payload: taggSchema, collection) -> bool:
    from backend.app.db.database import processed_collection

    # We combine the ID, status, AND the specific timestamp into one query
    query = {
        "_id": ObjectId(payload.tweet_id),
        "status": "tagging",
        "locked_at": payload.locked_at,  # This is the "Security Guard"
    }

    tweet = await collection.find_one_and_update(
        query,
        {
            "$set": {
                "status": "tagged",
                "is_dangerous": payload.is_dangerous,
                "category": payload.category,
                "tagged_by": payload.tagged_by,
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    # If 'tweet' is None, it means:
    # 1. The ID is wrong OR
    # 2. The status isn't 'tagging' OR
    # 3. Someone else locked it (the locked_at changed)
    if not tweet:
        raise ValueError(
            "Submission failed: Lock is invalid or has been taken by another user."
        )

    # Move to processed and wipe from working
    await processed_collection.insert_one(tweet)
    await collection.delete_one({"_id": tweet["_id"]})

    return True


async def escalate_tweet(payload: esclateSchema):
    query = {
        "_id": ObjectId(payload.tweet_id),
        "status": "tagging",
        "locked_at": payload.locked_at,
    }

    # 1. Just find it first to make sure the lock is still valid
    tweet = await working_collection.find_one(query)

    if not tweet:
        raise ValueError(
            "Escalation failed: Lock is invalid or has been taken by another user."
        )

    # 2. Reset the status manually in the dictionary before inserting
    tweet["status"] = "pending"
    tweet["locked_at"] = None

    # 3. Move it
    await escalation_collection.insert_one(tweet)
    await working_collection.delete_one({"_id": tweet["_id"]})

    return True


async def release_stale_locks(collection):
    timeout_limit = int(os.getenv("TIMEOUT_LIMIT", "300"))
    while True:
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(seconds=timeout_limit)

        # Let's see one tweet that it's NOT catching
        sample = await collection.find_one({"status": "tagging"})
        if sample:
            l_at = sample.get("locked_at")
            # If this prints, compare l_at to the Cutoff printed above

        result = await collection.update_many(
            {"status": "tagging", "locked_at": {"$lt": cutoff_time}},
            {"$set": {"status": "pending", "locked_at": None}},
        )

        if result.modified_count > 0:
            print(f"✅ SUCCESS: Released {result.modified_count} stale tweets.")

        await asyncio.sleep(60)


async def release_tweet(id, collection):
    result = await collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": "pending", "locked_at": None}}
    )
    if result.matched_count > 0:
        print(f"✅ SUCCESS: Released stale tweets.")
        return True
    else:
        print(f"failed to find tweet")
        return False
