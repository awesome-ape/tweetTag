from email import header
from backend.app.db.database import (
    working_collection,
    escalation_collection,
    processed_collection,
)
from backend.app.services.tweets import tagger
from backend.app.schemas.tweet_scheme import TweetinDB, taggSchemaFront
from fastapi import APIRouter, HTTPException, Depends, Header
from backend.app.schemas.tweet_scheme import taggSchema, esclateSchema
from backend.app.services.users.users import is_admin
from backend.app.db.database import working_collection
from backend.app.dependencies.auth import get_current_user
from backend.app.services.tweets.tagger import release_tweet


router = APIRouter()


@router.get("/claim_tweet", response_model=TweetinDB)
async def get_tweet(current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    tweet = await tagger.claim_tweet(working_collection)
    if not tweet:
        raise HTTPException(status_code=404, detail="No tweet available for tagging")
    return tweet


@router.post("/submit_tagged_tweet")
async def submit_tagged_tweet(
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
    sucsess = await tagger.submit_tagged_tweet(new_payload, working_collection)
    if not sucsess:
        raise HTTPException(status_code=400, detail="Failed to submit tagged tweet")
    return {"message": "Tagged tweet submitted successfully"}


@router.post("/escalate_tweet")
async def escalate_tweet(
    payload: esclateSchema, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    sucsess = await tagger.escalate_tweet(payload)
    if not sucsess:
        raise HTTPException(status_code=400, detail="Failed to escalate tweet")
    return {"message": "Tweet escalated successfully"}


@router.put("/release_working_tweet")
async def on_release_working(tweet_id: str, current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Directly uses the working_collection imported from your DB file
    success = await release_tweet(tweet_id, working_collection)

    if not success:
        raise HTTPException(
            status_code=400, detail="Tweet not found in working or already released"
        )

    return {"message": "Working tweet released successfully"}


@router.put("/release_escalated_tweet")
async def on_release_escalated(tweet_id: str, current_user=Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Uses the escalation_collection (make sure this is imported at the top)
    success = await release_tweet(tweet_id, escalation_collection)

    if not success:
        raise HTTPException(
            status_code=400, detail="Tweet not found in escalation or already released"
        )

    return {"message": "Escalated tweet released successfully"}
