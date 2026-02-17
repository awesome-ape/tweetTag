import asyncio
from bson import ObjectId
from unittest import result
from backend.app.db.database import (
    backup_collection,
    escalation_collection,
    working_collection,
    processed_collection,
    users_collection,
)
from backend.app.schemas.tweet_scheme import TweetinDB
from typing import List
from dotenv import load_dotenv
import os
from typing import List, Dict
from pathlib import Path
from typing import List, Tuple


base_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")


async def get_processed_tweets(page: int = 1):
    # Ensure page_size is pulled correctly
    page_size = int(os.getenv("PAGE_SIZE", 10))

    pipeline = [
        # 1. Sort and Paginate FIRST (Performance)
        {"$sort": {"locked_at": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
        # 2. CONVERT String ID to ObjectId (Crucial Fix)
        {"$addFields": {"tagged_by_obj": {"$toObjectId": "$tagged_by"}}},
        # 3. The "Join" using the converted ID
        {
            "$lookup": {
                "from": "users",
                "localField": "tagged_by_obj",  # Use the converted field
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        # 4. Flatten the result (with safety)
        {
            "$unwind": {
                "path": "$user_info",
                "preserveNullAndEmptyArrays": True,  # Don't delete tweet if user not found
            }
        },
    ]

    cursor = processed_collection.aggregate(pipeline)
    results = []

    async for doc in cursor:
        # doc now contains BOTH tweet and user_info
        tweet = TweetinDB.from_mongo(doc)
        username = doc["user_info"]["username"]
        results.append((tweet, username))

    return results


async def get_leaderboard() -> List[Dict]:
    pipeline = [
        {"$group": {"_id": "$tagged_by", "total_processed": {"$sum": 1}}},
        {"$sort": {"total_processed": -1}},
        {"$addFields": {"user_id_obj": {"$toObjectId": "$_id"}}},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id_obj",
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        {"$unwind": "$user_info"},
        {
            "$project": {
                "username": "$user_info.username",
                "total_processed": 1,
                "_id": 0,
            }
        },
    ]

    # .to_list(length=None) fetches all results from the cursor into a Python list
    cursor = processed_collection.aggregate(pipeline)
    results = await cursor.to_list(length=None)

    return results


async def get_header_data(user_id: str) -> Dict:
    try:
        # 1. Count processed tweets (using string ID as stored in tagged_by)
        uid_string = str(user_id).strip()
        print(f"DEBUG: Variable value is '{uid_string}'")
        processed_count = await processed_collection.count_documents(
            {"tagged_by": uid_string}
        )

        # 2. Look up the username (converting string to ObjectId for the users table)
        # We only include the 'username' field and exclude '_id'
        user_doc = await users_collection.find_one(
            {"_id": ObjectId(user_id)}, {"username": 1, "_id": 0}
        )

        if not user_doc:
            return {"username": "Unknown", "processed_count": processed_count}

        return {
            "username": user_doc.get("username"),
            "processed_count": processed_count,
        }

    except Exception as e:
        print(f"Error in get_header_data: {e}")
        return {"username": "Error", "processed_count": 0}
