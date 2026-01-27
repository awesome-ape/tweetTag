import asyncio
from unittest import result
from app.db.database import backup_collection, escalation_collection, working_collection, processed_collection
from app.schemas.tweet_scheme import TweetinDB,TweetSchema, taggSchema,esclateSchema
from typing import List
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from pathlib import Path
from pymongo import ReturnDocument
from bson import ObjectId
from app.services.tweets.tagger import claim_tweet, submit_tagged_tweet
from app.services.users.users import is_admin

base_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")

async def get_escalated_tweets() -> List[TweetinDB]:
    tweets_data = escalation_collection.find({})
    tweets = []
    async for tweet_data in tweets_data:
        tweet = TweetinDB.from_mongo(tweet_data)
        if tweet:
            tweets.append(tweet)
    return tweets

async def claim_escalated_tweet(tweet_id: str) -> TweetinDB | None:
    timeout_limit = int(os.getenv("TIMEOUT_LIMIT", "300"))
    expiry_time = datetime.now(timezone.utc) - timedelta(seconds=timeout_limit)

    # 1. Fixed syntax: Added () and converted to ObjectId
    # 2. Used 'escalation_collection' specifically
    query = {
        "_id": ObjectId(tweet_id), 
        "$or": [
            {"status": "pending"},
            {"status": "tagging", "locked_at": {"$lt": expiry_time}}
        ]
    }

    update = {
        "$set": { 
            "status": "tagging", 
            "locked_at": datetime.now(timezone.utc) 
        }
    }

    # Use the escalation_collection directly here
    tweet_data = await escalation_collection.find_one_and_update(
        query,
        update,
        return_document=ReturnDocument.AFTER
    )

    if not tweet_data:
        return None

    return TweetinDB.from_mongo(tweet_data)

async def submit_escalated_tagged_tweet(payload: taggSchema) -> bool:
    return await submit_tagged_tweet(payload, escalation_collection)