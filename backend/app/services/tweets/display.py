import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bson import ObjectId
from dotenv import load_dotenv

from backend.app.db.database import processed_collection, users_collection
from backend.app.schemas.tweet_scheme import TweetinDB

base_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")


async def get_processed_tweets(page: int = 1) -> List[Tuple[TweetinDB, Optional[str]]]:
    """
    Returns: [(TweetinDB, tagged_by_username or None), ...]
    """
    page_size = int(os.getenv("PAGE_SIZE", "10"))

    pipeline = [
        {"$sort": {"locked_at": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},

        # Normalize tagged_by -> ObjectId (supports: ObjectId / string / null)
        {
            "$addFields": {
                "tagged_by_obj": {
                    "$switch": {
                        "branches": [
                            # already ObjectId
                            {"case": {"$eq": [{"$type": "$tagged_by"}, "objectId"]}, "then": "$tagged_by"},
                            # string ObjectId
                            {
                                "case": {
                                    "$and": [
                                        {"$eq": [{"$type": "$tagged_by"}, "string"]},
                                        {"$ne": ["$tagged_by", ""]},
                                        {"$ne": ["$tagged_by", None]},
                                    ]
                                },
                                "then": {"$toObjectId": "$tagged_by"},
                            },
                        ],
                        "default": None,
                    }
                }
            }
        },

        {
            "$lookup": {
                "from": "users",
                "localField": "tagged_by_obj",
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
    ]

    cursor = processed_collection.aggregate(pipeline)

    results: List[Tuple[TweetinDB, Optional[str]]] = []
    async for doc in cursor:
        tweet = TweetinDB.from_mongo(doc)

        username: Optional[str] = None
        ui = doc.get("user_info")
        if isinstance(ui, dict):
            username = ui.get("username")

        results.append((tweet, username))

    return results


async def get_leaderboard() -> List[Dict]:
    """
    Returns:
    [{ "username": <str>, "total_processed": <int> }, ...]
    """

    pipeline = [
        # Normalize tagged_by -> ObjectId for grouping (supports ObjectId/string/null)
        {
            "$addFields": {
                "tagged_by_obj": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": [{"$type": "$tagged_by"}, "objectId"]}, "then": "$tagged_by"},
                            {
                                "case": {
                                    "$and": [
                                        {"$eq": [{"$type": "$tagged_by"}, "string"]},
                                        {"$ne": ["$tagged_by", ""]},
                                        {"$ne": ["$tagged_by", None]},
                                    ]
                                },
                                "then": {"$toObjectId": "$tagged_by"},
                            },
                        ],
                        "default": None,
                    }
                }
            }
        },

        # Group by normalized object id
        {"$group": {"_id": "$tagged_by_obj", "total_processed": {"$sum": 1}}},
        {"$sort": {"total_processed": -1}},

        # Lookup username
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},

        # Project output (username not id)
        {
            "$project": {
                "_id": 0,
                "username": {"$ifNull": ["$user_info.username", "Unknown"]},
                "total_processed": 1,
            }
        },
    ]

    cursor = processed_collection.aggregate(pipeline)
    results = await cursor.to_list(length=None)
    return results


async def get_header_data(user_id: str) -> Dict:
    """
    Returns: {"username": str, "processed_count": int}
    """
    uid_string = str(user_id).strip()

    processed_count = await processed_collection.count_documents({"tagged_by": uid_string})

    # Safe ObjectId conversion
    try:
        oid = ObjectId(uid_string)
    except Exception:
        return {"username": "Unknown", "processed_count": processed_count}

    user_doc = await users_collection.find_one({"_id": oid}, {"username": 1, "_id": 0})
    if not user_doc:
        return {"username": "Unknown", "processed_count": processed_count}

    return {"username": user_doc.get("username", "Unknown"), "processed_count": processed_count}