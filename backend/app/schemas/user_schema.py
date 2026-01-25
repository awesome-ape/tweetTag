from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class UserSchema(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: str
    isADMIN: Optional[bool] = False
    password: str


    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )