import os
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from bson import ObjectId
from dotenv import load_dotenv

from backend.app.db.database import processed_collection, users_collection
from backend.app.schemas.tweet_scheme import TweetinDB

env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


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


def _tagged_by_obj_add_fields_stage() -> Dict[str, Any]:
    return {
        "$addFields": {
            "tagged_by_obj": {
                "$switch": {
                    "branches": [
                        {
                            "case": {"$eq": [{"$type": "$tagged_by"}, "objectId"]},
                            "then": "$tagged_by",
                        },
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
    }


def _user_match_query(user_id: str) -> Dict[str, Any]:
    user_id = str(user_id).strip()

    candidates: List[Any] = [user_id]
    try:
        candidates.append(ObjectId(user_id))
    except Exception:
        pass

    return {"tagged_by": {"$in": candidates}}


def _stats_base_match() -> Dict[str, Any]:
    return {
        **_tagged_query(),
        "tagged_at": {"$ne": None},
    }


def _normalize_category_name(category: Any) -> str:
    if category is None:
        return "Uncategorized"

    category_str = str(category).strip()
    return category_str if category_str else "Uncategorized"


async def get_processed_tweets(page: int = 1) -> List[Tuple[TweetinDB, Optional[str]]]:
    """
    Legacy: Returns only TAGGED tweets:
    [(TweetinDB, tagged_by_username or None), ...]
    """
    page_size = _get_page_size()
    if page < 1:
        page = 1

    pipeline = [
        {"$match": _tagged_query()},
        {"$sort": {"tagged_at": -1, "_id": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
        _tagged_by_obj_add_fields_stage(),
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

    total = await processed_collection.count_documents(query)
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    print(f"DEBUG: Total from DB: {total}, Page Size: {page_size}")

    if page > total_pages:
        return {
            "items": [],
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": total_pages,
        }

    pipeline = [
        {"$match": query},
        {"$sort": {"tagged_at": -1, "_id": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
        _tagged_by_obj_add_fields_stage(),
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
    """
    pipeline = [
        _tagged_by_obj_add_fields_stage(),
        {"$match": {"tagged_by_obj": {"$ne": None}}},
        {"$group": {"_id": "$tagged_by_obj", "total_processed": {"$sum": 1}}},
        {"$sort": {"total_processed": -1}},
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
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


async def get_daily_tagging_stats() -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns grouped by date:
    {
      "2026-04-15": [
        { "username": "almog", "count": 18 },
        { "username": "dana", "count": 11 }
      ],
      ...
    }
    """
    pipeline = [
        {"$match": {**_tagged_query(), "tagged_at": {"$ne": None}}},
        _tagged_by_obj_add_fields_stage(),
        {"$match": {"tagged_by_obj": {"$ne": None}}},
        {
            "$group": {
                "_id": {
                    "user_id": "$tagged_by_obj",
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$tagged_at",
                        }
                    },
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "_id.user_id",
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "date": "$_id.date",
                "username": {"$ifNull": ["$user_info.username", "Unknown"]},
                "count": 1,
                "_id": 0,
            }
        },
        {
            "$group": {
                "_id": "$date",
                "users": {
                    "$push": {
                        "username": "$username",
                        "count": "$count",
                    }
                },
            }
        },
        {"$sort": {"_id": -1}},
    ]

    cursor = processed_collection.aggregate(pipeline)
    raw_results = await cursor.to_list(length=None)

    return {doc["_id"]: doc["users"] for doc in raw_results}


async def get_tagging_distribution_stats() -> Dict[str, Any]:
    """
    Returns:
    {
      "total": {
        "dangerous": {
          "count": 12,
          "categories": {
            "Gas": 5,
            "Oil": 4
          }
        },
        "safe": {
          "count": 20,
          "categories": {
            "Unrelated": 12,
            "Gas": 3
          }
        }
      },
      "by_day": {
        "2026-04-15": {
          "dangerous": {
            "count": 4,
            "categories": {
              "Gas": 2,
              "Oil": 2
            }
          },
          "safe": {
            "count": 7,
            "categories": {
              "Unrelated": 4,
              "Electricity": 3
            }
          }
        }
      }
    }
    """
    query = _stats_base_match()

    total_pipeline = [
        {"$match": query},
        {
            "$project": {
                "is_dangerous": "$is_dangerous",
                "category": {
                    "$cond": [
                        {
                            "$or": [
                                {"$eq": ["$category", None]},
                                {"$eq": [{"$trim": {"input": {"$ifNull": ["$category", ""]}}}, ""]},
                            ]
                        },
                        None,
                        "$category",
                    ]
                },
            }
        },
        {
            "$facet": {
                "dangerous_count": [
                    {"$match": {"is_dangerous": True, "category": {"$ne": None}}},
                    {"$count": "count"},
                ],
                "dangerous_categories": [
                    {"$match": {"is_dangerous": True, "category": {"$ne": None}}},
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1, "_id": 1}},
                ],
                "safe_count": [
                    {"$match": {"is_dangerous": False}},
                    {"$count": "count"},
                ],
                "safe_categories": [
                    {"$match": {"is_dangerous": False}},
                    {"$project": {"category": {"$ifNull": ["$category", "Uncategorized"]}}},
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1, "_id": 1}},
                ],
            }
        },
    ]

    by_day_pipeline = [
        {"$match": query},
        {
            "$project": {
                "date": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$tagged_at",
                    }
                },
                "is_dangerous": "$is_dangerous",
                "category": {
                    "$cond": [
                        {
                            "$or": [
                                {"$eq": ["$category", None]},
                                {"$eq": [{"$trim": {"input": {"$ifNull": ["$category", ""]}}}, ""]},
                            ]
                        },
                        None,
                        "$category",
                    ]
                },
            }
        },
        {
            "$facet": {
                "dangerous_count_by_day": [
                    {"$match": {"is_dangerous": True, "category": {"$ne": None}}},
                    {"$group": {"_id": "$date", "count": {"$sum": 1}}},
                    {"$sort": {"_id": -1}},
                ],
                "dangerous_categories_by_day": [
                    {"$match": {"is_dangerous": True, "category": {"$ne": None}}},
                    {"$group": {"_id": {"date": "$date", "category": "$category"}, "count": {"$sum": 1}}},
                    {"$sort": {"_id.date": -1, "count": -1, "_id.category": 1}},
                ],
                "safe_count_by_day": [
                    {"$match": {"is_dangerous": False}},
                    {"$group": {"_id": "$date", "count": {"$sum": 1}}},
                    {"$sort": {"_id": -1}},
                ],
                "safe_categories_by_day": [
                    {"$match": {"is_dangerous": False}},
                    {"$project": {"date": 1, "category": {"$ifNull": ["$category", "Uncategorized"]}}},
                    {"$group": {"_id": {"date": "$date", "category": "$category"}, "count": {"$sum": 1}}},
                    {"$sort": {"_id.date": -1, "count": -1, "_id.category": 1}},
                ],
            }
        },
    ]

    total_raw = await processed_collection.aggregate(total_pipeline).to_list(length=1)
    by_day_raw = await processed_collection.aggregate(by_day_pipeline).to_list(length=1)

    total_doc = total_raw[0] if total_raw else {}
    by_day_doc = by_day_raw[0] if by_day_raw else {}

    dangerous_total_count = ((total_doc.get("dangerous_count") or [{}])[0]).get("count", 0)
    safe_total_count = ((total_doc.get("safe_count") or [{}])[0]).get("count", 0)

    dangerous_total_categories = {
        _normalize_category_name(item.get("_id")): int(item.get("count", 0))
        for item in (total_doc.get("dangerous_categories") or [])
    }

    safe_total_categories = {
        _normalize_category_name(item.get("_id")): int(item.get("count", 0))
        for item in (total_doc.get("safe_categories") or [])
    }

    total_result = {
        "dangerous": {
            "count": int(dangerous_total_count),
            "categories": dangerous_total_categories,
        },
        "safe": {
            "count": int(safe_total_count),
            "categories": safe_total_categories,
        },
    }

    by_day_result: Dict[str, Dict[str, Any]] = {}

    def ensure_day(day_key: str) -> None:
        if day_key not in by_day_result:
            by_day_result[day_key] = {
                "dangerous": {"count": 0, "categories": {}},
                "safe": {"count": 0, "categories": {}},
            }

    for item in by_day_doc.get("dangerous_count_by_day") or []:
        day_key = item.get("_id")
        if not day_key:
            continue
        ensure_day(day_key)
        by_day_result[day_key]["dangerous"]["count"] = int(item.get("count", 0))

    for item in by_day_doc.get("dangerous_categories_by_day") or []:
        item_id = item.get("_id", {})
        day_key = item_id.get("date")
        category_key = _normalize_category_name(item_id.get("category"))
        if not day_key:
            continue
        ensure_day(day_key)
        by_day_result[day_key]["dangerous"]["categories"][category_key] = int(item.get("count", 0))

    for item in by_day_doc.get("safe_count_by_day") or []:
        day_key = item.get("_id")
        if not day_key:
            continue
        ensure_day(day_key)
        by_day_result[day_key]["safe"]["count"] = int(item.get("count", 0))

    for item in by_day_doc.get("safe_categories_by_day") or []:
        item_id = item.get("_id", {})
        day_key = item_id.get("date")
        category_key = _normalize_category_name(item_id.get("category"))
        if not day_key:
            continue
        ensure_day(day_key)
        by_day_result[day_key]["safe"]["categories"][category_key] = int(item.get("count", 0))

    return {
        "total": total_result,
        "by_day": by_day_result,
    }


async def get_user_impact_stats(user_id: str) -> Dict[str, Any]:
    """
    Returns the current user's personal impact stats:
    {
      "total_tagged": 25,
      "dangerous": {
        "count": 8,
        "categories": {
          "Gas": 3,
          "Oil": 5
        }
      },
      "safe": {
        "count": 17,
        "categories": {
          "Unrelated": 10,
          "Electricity": 4,
          "Uncategorized": 3
        }
      }
    }
    """
    query = {
        **_stats_base_match(),
        **_user_match_query(user_id),
    }

    pipeline = [
        {"$match": query},
        {
            "$project": {
                "is_dangerous": "$is_dangerous",
                "category": {
                    "$cond": [
                        {
                            "$or": [
                                {"$eq": ["$category", None]},
                                {"$eq": [{"$trim": {"input": {"$ifNull": ["$category", ""]}}}, ""]},
                            ]
                        },
                        None,
                        "$category",
                    ]
                },
            }
        },
        {
            "$facet": {
                "total_tagged": [
                    {"$count": "count"},
                ],
                "dangerous_count": [
                    {"$match": {"is_dangerous": True, "category": {"$ne": None}}},
                    {"$count": "count"},
                ],
                "dangerous_categories": [
                    {"$match": {"is_dangerous": True, "category": {"$ne": None}}},
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1, "_id": 1}},
                ],
                "safe_count": [
                    {"$match": {"is_dangerous": False}},
                    {"$count": "count"},
                ],
                "safe_categories": [
                    {"$match": {"is_dangerous": False}},
                    {"$project": {"category": {"$ifNull": ["$category", "Uncategorized"]}}},
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1, "_id": 1}},
                ],
            }
        },
    ]

    raw = await processed_collection.aggregate(pipeline).to_list(length=1)
    doc = raw[0] if raw else {}

    total_tagged = ((doc.get("total_tagged") or [{}])[0]).get("count", 0)
    dangerous_count = ((doc.get("dangerous_count") or [{}])[0]).get("count", 0)
    safe_count = ((doc.get("safe_count") or [{}])[0]).get("count", 0)

    dangerous_categories = {
        _normalize_category_name(item.get("_id")): int(item.get("count", 0))
        for item in (doc.get("dangerous_categories") or [])
    }

    safe_categories = {
        _normalize_category_name(item.get("_id")): int(item.get("count", 0))
        for item in (doc.get("safe_categories") or [])
    }

    return {
        "total_tagged": int(total_tagged),
        "dangerous": {
            "count": int(dangerous_count),
            "categories": dangerous_categories,
        },
        "safe": {
            "count": int(safe_count),
            "categories": safe_categories,
        },
    }


async def get_user_daily_tagging_stats(user_id: str) -> List[Dict[str, Any]]:
    """
    Current user's stats by date.
    Returns:
    [
      { "date": "2026-04-15", "total_tagged": 7 },
      ...
    ]
    """
    pipeline = [
        {"$match": {**_tagged_query(), **_user_match_query(user_id), "tagged_at": {"$ne": None}}},
        {
            "$group": {
                "_id": {
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$tagged_at",
                        }
                    }
                },
                "total_tagged": {"$sum": 1},
            }
        },
        {"$sort": {"_id.date": -1}},
        {
            "$project": {
                "_id": 0,
                "date": "$_id.date",
                "total_tagged": 1,
            }
        },
    ]

    cursor = processed_collection.aggregate(pipeline)
    return await cursor.to_list(length=None)


async def get_header_data(user_id: str) -> Dict:
    """
    Returns: {"username": str, "processed_count": int}
    """
    uid_string = str(user_id).strip()

    processed_count = await processed_collection.count_documents(
        _user_match_query(uid_string)
    )

    try:
        oid = ObjectId(uid_string)
    except Exception:
        return {"username": "Unknown", "processed_count": processed_count}

    user_doc = await users_collection.find_one({"_id": oid}, {"username": 1, "_id": 0})
    if not user_doc:
        return {"username": "Unknown", "processed_count": processed_count}

    return {
        "username": user_doc.get("username", "Unknown"),
        "processed_count": processed_count,
    }
async def search_users_for_admin(query: str, limit: int = 8) -> List[Dict[str, str]]:
    query = (query or "").strip()
    if not query:
        return []

    regex = {"$regex": query, "$options": "i"}

    cursor = users_collection.find(
        {
            "$or": [
                {"username": regex},
                {"email": regex},
            ]
        },
        {
            "_id": 1,
            "username": 1,
            "email": 1,
        },
    ).sort("username", 1).limit(limit)

    results = await cursor.to_list(length=limit)

    return [
        {
            "id": str(doc["_id"]),
            "username": doc.get("username", "Unknown"),
            "email": doc.get("email", ""),
        }
        for doc in results
    ]
async def get_user_tagged_tweets_paginated_for_admin(
    user_id: str,
    page: int = 1,
) -> Dict[str, Any]:
    page_size = _get_page_size()
    if page < 1:
        page = 1

    query = {
        "$and": [
            _tagged_query(),
            _user_match_query(user_id),
        ]
    }

    total = await processed_collection.count_documents(query)
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

    if page > total_pages:
        return {
            "items": [],
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": total_pages,
        }

    pipeline = [
        {"$match": query},
        {"$sort": {"tagged_at": -1, "_id": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
        _tagged_by_obj_add_fields_stage(),
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
