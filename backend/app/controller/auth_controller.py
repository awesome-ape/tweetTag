from fastapi import APIRouter, HTTPException
from app.services.auth_service import register_user
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


@router.post("/register")
async def register(request: RegisterRequest):
    try:
        user = await register_user(
            username=request.username,
            email=request.email,
            password=request.password
        )
        return {
            "message": "User created successfully",
            "user": user
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
