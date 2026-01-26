from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class TweetSchema(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    content: str
    created_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


class TweetinDB(TweetSchema):
    status: str ="pending"
    locked_at: Optional[datetime] = None
    tagged_by: Optional[str] = None
    is_dangerous: Optional[bool] = None
    category: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @classmethod
    def from_mongo(cls, data: dict):
         if not data:
             return None
         if "_id" in data:
             data["_id"] = str(data["_id"])
         return cls(**data)
      # e.g., "pending", "tagged", etc.
class taggSchema(BaseModel):
    tweet_id: str
    is_dangerous: bool
    category: str
    tagged_by: str
    locked_at: datetime
    model_config = ConfigDict(arbitrary_types_allowed=True)

class esclateSchema(BaseModel):
    tweet_id: str
    locked_at: datetime
    model_config = ConfigDict(arbitrary_types_allowed=True)

