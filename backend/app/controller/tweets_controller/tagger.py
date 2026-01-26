from app.services.tweets import tagger
from app.schemas.tweet_scheme import TweetinDB
from fastapi import APIRouter, HTTPException,Depends
from app.schemas.tweet_scheme import taggSchema,esclateSchema


router = APIRouter()


@router.get("/claim_tweet", response_model=TweetinDB)
async def get_tweet() :
    tweet= await tagger.claim_tweet()
    if not tweet:
        raise HTTPException(status_code=404, detail="No tweet available for tagging")
    return tweet


@router.post("/submit_tagged_tweet")
async def submit_tagged_tweet(payload: taggSchema):
    sucsess = await tagger.submit_tagged_tweet(payload)
    if not sucsess:
        raise HTTPException(status_code=400, detail="Failed to submit tagged tweet")
    return {"message": "Tagged tweet submitted successfully"}


@router.post("/escalate_tweet")
async def escalate_tweet(payload: esclateSchema):
    sucsess = await tagger.escalate_tweet(payload)
    if not sucsess:
        raise HTTPException(status_code=400, detail="Failed to escalate tweet")
    return {"message": "Tweet escalated successfully"}
