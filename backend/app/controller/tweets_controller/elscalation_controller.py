from fastapi import APIRouter, Depends, HTTPException

from backend.app.dependencies.auth import get_current_user
from backend.app.schemas.tweet_scheme import TweetinDB, taggSchemaFront, taggSchema, esclateSchema
from backend.app.services.tweets import esclation
from backend.app.services.users.users import is_admin

router = APIRouter()


@router.get("/get_escalated_tweets", response_model=list[TweetinDB])
async def get_escalated_tweets(current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    return await esclation.get_escalated_tweets()


@router.get("/claim_escalated_tweet", response_model=TweetinDB)
async def claim_escalated_tweet(tweet_id: str, current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    tweet = await esclation.claim_escalated_tweet(tweet_id=tweet_id, user_id=str(user_id))
    if not tweet:
        raise HTTPException(
            status_code=404,
            detail="Tweet is not available (locked by another admin or not found).",
        )
    return tweet


@router.post("/submit_escalated_tagged_tweet")
async def submit_escalated_tagged_tweet(payload: taggSchemaFront, current_user=Depends(get_current_user)):
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

    try:
        await esclation.submit_escalated_tagged_tweet(new_payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"detail": "Tagged tweet submitted successfully"}


@router.post("/release_escalated_lock")
async def release_escalated_lock(payload: esclateSchema, current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    ok = await esclation.release_escalated_lock(payload.tweet_id, str(user_id))
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to release lock")

    return {"detail": "Lock released"}