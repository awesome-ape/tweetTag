from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(request: RegisterRequest):
    try:
        return await register_user(
            request.username,
            request.email,
            request.password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(request: LoginRequest):
    try:
        return await login_user(
            request.username,
            request.password
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
