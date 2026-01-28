from http.client import HTTPException

from fastapi.params import Header
from app.schemas.tweet_scheme import TweetinDB, taggSchema, taggSchemaFront
from app.services.tweets import esclation
from app.services.users.users import is_admin
from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/get_escalated_tweets", response_model=list[TweetinDB])
async def get_escalated_tweets(current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")
    tweets = await esclation.get_escalated_tweets()
    return tweets


@router.get("/claim_escalated_tweet", response_model=TweetinDB)
async def claim_escalated_tweet(
    current_user=Depends(get_current_user), tweet_id: str = Header(...)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")
    tweet = await esclation.claim_escalated_tweet(tweet_id)
    if not tweet:
        raise HTTPException(
            status_code=404,
            detail="the tweet isnt available for escalation tagging another admin may be currently tagging it",
        )
    return tweet


@router.post("/submit_escalated_tagged_tweet")
async def submit_escalated_tagged_tweet(
    payload: taggSchemaFront, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")
    new_payload = taggSchema(
        tweet_id=payload.tweet_id,
        is_dangerous=payload.is_dangerous,
        category=payload.category,
        tagged_by=str(user_id),
        locked_at=payload.locked_at,
    )
    result = await esclation.submit_escalated_tagged_tweet(new_payload)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to submit tagged tweet")
    return {"detail": "Tagged tweet submitted successfully"}
