import os
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from bson import ObjectId
from dotenv import load_dotenv

from backend.app.db.database import processed_collection, users_collection
from backend.app.schemas.tweet_scheme import TweetinDB

base_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")


def _get_page_size() -> int:
    """
    Use PAGE_SIZE from .env. Recommended: PAGE_SIZE=50
    """
    try:
        return max(1, int(os.getenv("PAGE_SIZE", "50")))
    except Exception:
        return 50


def _tagged_query() -> Dict[str, Any]:
    """
    Defines what counts as a "tagged" tweet.
    Mirrors your frontend isTaggedTweet logic:
    - status === "tagged"
    - OR tagged_by exists (not empty)
    - OR is_dangerous is boolean
    - OR category exists (not empty)
    """
    return {
        "$or": [
            {"status": "tagged"},
            {"tagged_by": {"$exists": True, "$nin": [None, ""]}},
            {"is_dangerous": {"$in": [True, False]}},
            {"category": {"$exists": True, "$nin": [None, ""]}},
        ]
    }


async def get_processed_tweets(page: int = 1) -> List[Tuple[TweetinDB, Optional[str]]]:
    """
    Legacy: Returns only TAGGED tweets:
    [(TweetinDB, tagged_by_username or None), ...]
    """
    page_size = _get_page_size()
    if page < 1:
        page = 1

    pipeline = [
        {"$match": _tagged_query()},  # ✅ ONLY tagged
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


async def get_processed_tweets_paginated(page: int = 1) -> Dict[str, Any]:
    """
    Returns ONLY TAGGED tweets with pagination metadata:
    {
      "items": [(TweetinDB, tagged_by_username or None), ...],
      "page": <int>,
      "pageSize": <int>,
      "total": <int>,
      "totalPages": <int>,
    }
    """
    page_size = _get_page_size()
    if page < 1:
        page = 1

    query = _tagged_query()

    # ✅ total count of TAGGED only
    total = await processed_collection.count_documents(query)
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

    # If user asks for page beyond end, return empty items but keep metadata
    if page > total_pages:
        return {
            "items": [],
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": total_pages,
        }

    pipeline = [
        {"$match": query},  # ✅ ONLY tagged
        {"$sort": {"locked_at": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},

        # Normalize tagged_by -> ObjectId (supports: ObjectId / string / null)
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

    items: List[Tuple[TweetinDB, Optional[str]]] = []
    async for doc in cursor:
        tweet = TweetinDB.from_mongo(doc)

        username: Optional[str] = None
        ui = doc.get("user_info")
        if isinstance(ui, dict):
            username = ui.get("username")

        items.append((tweet, username))

    return {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPages": total_pages,
    }


async def get_leaderboard() -> List[Dict]:
    """
    Returns:
    [{ "username": <str>, "total_processed": <int> }, ...]

    NOTE: This currently counts ALL processed_collection docs with tagged_by set.
    If you want leaderboard to count ONLY tagged tweets, we can add the same query filter.
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