# backend/app/controller/tweets_controller/display_controller.py

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


@router.get(
    "/get_tweets_for_display",
    response_model=List[Tuple[TweetinDB, Optional[str]]],
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

    return await display.get_processed_tweets(page=page)


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

    # display.get_leaderboard() צריך להחזיר:
    # [{ "username": "...", "total_processed": 12 }, ...]
    return await display.get_leaderboard()


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

    data = await display.get_header_data(user_id)
    data["isADMIN"] = bool(current_user.get("isADMIN", False))
    return data