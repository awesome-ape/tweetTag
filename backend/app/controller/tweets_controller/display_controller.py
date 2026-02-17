from backend.app.services.tweets import display

from backend.app.schemas.tweet_scheme import TweetinDB
from fastapi import APIRouter, Depends, HTTPException, Header

from backend.app.services.users.users import is_admin

from backend.app.dependencies.auth import get_current_user
from backend.app.schemas.user_schema import UserResponse


router = APIRouter()


@router.get("/get_tweets_for_display", response_model=list[tuple[TweetinDB, str]])
async def get_tweets_for_display(
    current_user=Depends(get_current_user),
    page: int = 1,
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")
    tweets_with_usernames = await display.get_processed_tweets(page=page)
    return tweets_with_usernames


@router.get("/get_tagging_leaderboard", response_model=list[dict])
async def get_tagging_leaderboaard(current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")
    leaderboard = await display.get_leaderboard()
    return leaderboard


@router.get("/get_header_data")
async def get_header_data(current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    data = await display.get_header_data(user_id)
    return data
