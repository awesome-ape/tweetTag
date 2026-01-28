from email import header
from app.services.tweets import tagger
from app.schemas.tweet_scheme import TweetinDB, taggSchemaFront
from fastapi import APIRouter, HTTPException, Depends, Header
from app.schemas.tweet_scheme import taggSchema, esclateSchema
from app.services.users.users import is_admin
from app.db.database import working_collection
from app.dependencies.auth import get_current_user


router = APIRouter()


@router.get("/claim_tweet", response_model=TweetinDB)
async def get_tweet():
    tweet = await tagger.claim_tweet(working_collection)
    if not tweet:
        raise HTTPException(status_code=404, detail="No tweet available for tagging")
    return tweet


@router.post("/submit_tagged_tweet")
async def submit_tagged_tweet(
    payload: taggSchemaFront, current_user=Depends(get_current_user)
):
    user_id = current_user.get("_id")
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
async def escalate_tweet(payload: esclateSchema):
    sucsess = await tagger.escalate_tweet(payload)
    if not sucsess:
        raise HTTPException(status_code=400, detail="Failed to escalate tweet")
    return {"message": "Tweet escalated successfully"}
