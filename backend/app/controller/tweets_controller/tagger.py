from fastapi import APIRouter, HTTPException, Depends

from backend.app.db.database import working_collection
from backend.app.db.database import processed_collection

from backend.app.dependencies.auth import get_current_user
from backend.app.schemas.tweet_scheme import (
    TweetinDB,
    taggSchemaFront,
    taggSchema,
    esclateSchema,
)
from backend.app.services.tweets import tagger
from backend.app.services.users.users import is_admin

router = APIRouter()


@router.get("/claim_tweet", response_model=TweetinDB)
async def claim_tweet_endpoint(current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    tweet = await tagger.claim_tweet(working_collection, user_id=str(user_id))
    if not tweet:
        raise HTTPException(status_code=404, detail="No tweet available for tagging")
    return tweet


@router.post("/submit_tagged_tweet")
async def submit_tagged_tweet_endpoint(
    payload: taggSchemaFront, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_payload = taggSchema(
        tweet_id=payload.tweet_id,
        is_dangerous=payload.is_dangerous,
        category=payload.category,
        tagged_by=str(user_id),
        locked_at=payload.locked_at,
    )

    try:
        await tagger.submit_tagged_tweet(new_payload, working_collection)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Tagged tweet submitted successfully"}


@router.post("/escalate_tweet")
async def escalate_tweet_endpoint(
    payload: esclateSchema, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        await tagger.escalate_tweet(payload, user_id=str(user_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Tweet escalated successfully"}


@router.post("/release_tweet_lock")
async def release_tweet_lock_endpoint(
    payload: esclateSchema, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ok = await tagger.release_lock(payload.tweet_id, str(user_id), working_collection)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to release lock")
    return {"detail": "Lock released"}


@router.get("/my_tagged_tweets", response_model=list[TweetinDB])
async def get_my_tagged_tweets_endpoint(
    limit: int = 200,
    current_user=Depends(get_current_user),
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await tagger.get_my_tagged_tweets(str(user_id), limit=limit)


@router.post("/release_processed_tweet_lock")
async def release_processed_tweet_lock_endpoint(
    payload: esclateSchema, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ok = await tagger.release_lock(payload.tweet_id, str(user_id), processed_collection)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to release lock")
    return {"detail": "Lock released"}


@router.get("/get_processed_tweet")
async def claim_processed_tweet_endpoint(
    tweet_id: str, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not await is_admin(user_id):
        raise HTTPException(status_code=403, detail="Forbidden: Admins only")

    tweet = await tagger.claim_processed_tweet(tweet_id, user_id)

    if not tweet:
        raise HTTPException(
            status_code=404,
            detail="Tweet is not available (locked by another admin or not found).",
        )

    return tweet


@router.put("/submit_edited_tweet")
async def submit_tagged_tweet_endpoint(
    payload: taggSchemaFront, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_payload = taggSchema(
        tweet_id=payload.tweet_id,
        is_dangerous=payload.is_dangerous,
        category=payload.category,
        tagged_by=str(user_id),
        locked_at=payload.locked_at,
    )

    try:
        await tagger.submit_tagged_tweet(new_payload, processed_collection)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Tweet edited successfully"}