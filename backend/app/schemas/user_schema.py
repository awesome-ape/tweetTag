from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class UserInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: str
    password: str
    isADMIN: bool = False

    model_config = ConfigDict(populate_by_name=True)


class UserResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: str
    isADMIN: bool

    model_config = ConfigDict(populate_by_name=True)
