from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Tuple

from backend.app.dependencies.auth import get_current_user
from backend.app.schemas.tweet_scheme import TweetinDB
from backend.app.services.tweets import display
from backend.app.services.users.users import is_admin

router = APIRouter()


class LeaderboardRow(BaseModel):
    username: str
    total_processed: int


class DailyUserCount(BaseModel):
    username: str
    count: int


class UserDailyTaggingRow(BaseModel):
    date: str
    total_tagged: int


class SeverityBucket(BaseModel):
    count: int
    categories: Dict[str, int]


class DayDistributionStats(BaseModel):
    dangerous: SeverityBucket
    safe: SeverityBucket


class TaggingDistributionResponse(BaseModel):
    total: DayDistributionStats
    by_day: Dict[str, DayDistributionStats]


class UserImpactStatsResponse(BaseModel):
    total_tagged: int
    dangerous: SeverityBucket
    safe: SeverityBucket


class PaginatedTweetsResponse(BaseModel):
    items: List[Tuple[TweetinDB, Optional[str]]]
    page: int
    pageSize: int
    total: int
    totalPages: int
class AdminUserSearchRow(BaseModel):
    id: str
    username: str
    email: str


class AdminUserTaggedTweetsResponse(BaseModel):
    items: List[Tuple[TweetinDB, Optional[str]]]
    page: int
    pageSize: int
    total: int
    totalPages: int
@router.get(
    "/get_tweets_for_display",
    response_model=PaginatedTweetsResponse,
)
async def get_tweets_for_display(
    current_user: Dict[str, Any] = Depends(get_current_user),
    page: int = 1,
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")

    return await display.get_processed_tweets_paginated(page=page)


@router.get(
    "/get_tagging_leaderboard",
    response_model=List[LeaderboardRow],
)
async def get_tagging_leaderboard(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    return await display.get_leaderboard()


@router.get(
    "/get_daily_tagging_stats",
    response_model=Dict[str, List[DailyUserCount]],
)
async def get_daily_tagging_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Admin only.
    Returns daily productivity grouped by date:
    {
      "2026-04-15": [
        { "username": "alice", "count": 12 },
        { "username": "bob", "count": 7 }
      ],
      ...
    }
    """
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    return await display.get_daily_tagging_stats()


@router.get(
    "/get_tagging_distribution_stats",
    response_model=TaggingDistributionResponse,
)
async def get_tagging_distribution_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Admin only.
    Returns separated dangerous/safe stats with counts and categories,
    both total and by day.
    """
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    return await display.get_tagging_distribution_stats()


@router.get(
    "/get_my_impact_stats",
    response_model=UserImpactStatsResponse,
)
async def get_my_impact_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns the current user's personal tagging impact:
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
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await display.get_user_impact_stats(str(user_id))


@router.get(
    "/get_my_daily_tagging_stats",
    response_model=List[UserDailyTaggingRow],
)
async def get_my_daily_tagging_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns the current user's own productivity by date:
    [
      { "date": "2026-04-15", "total_tagged": 7 },
      ...
    ]
    """
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await display.get_user_daily_tagging_stats(str(user_id))


@router.get("/get_header_data")
async def get_header_data(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns data for the Header component.
    Keeps: username, processed_count
    Adds: isADMIN
    """
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await display.get_header_data(str(user_id))
    data["isADMIN"] = bool(current_user.get("isADMIN", False))
    return data
@router.get(
    "/search_users_for_admin",
    response_model=List[AdminUserSearchRow],
)
async def search_users_for_admin(
    q: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    return await display.search_users_for_admin(q)


@router.get(
    "/get_user_impact_stats_admin",
    response_model=UserImpactStatsResponse,
)
async def get_user_impact_stats_admin(
    target_user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    return await display.get_user_impact_stats(target_user_id)


@router.get(
    "/get_user_daily_tagging_stats_admin",
    response_model=List[UserDailyTaggingRow],
)
async def get_user_daily_tagging_stats_admin(
    target_user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    return await display.get_user_daily_tagging_stats(target_user_id)


@router.get(
    "/get_user_tagged_tweets_for_admin",
    response_model=AdminUserTaggedTweetsResponse,
)
async def get_user_tagged_tweets_for_admin(
    target_user_id: str,
    page: int = 1,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")

    return await display.get_user_tagged_tweets_paginated_for_admin(
        user_id=target_user_id,
        page=page,
    )