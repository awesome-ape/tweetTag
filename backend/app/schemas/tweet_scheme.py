from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class TweetSchema(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    content: str
    created_at: datetime
    tagged_by: Optional[str] = None
    is_dangerous: Optional[bool] = None
    category: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )