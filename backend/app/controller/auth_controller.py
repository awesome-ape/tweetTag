from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.services.auth_service import (
    register_user,
    login_user,
    forgot_password,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=1)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1)


@router.post("/register")
async def register(request: RegisterRequest):
    try:
        return await register_user(request.username, request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        return await login_user(
            username=form_data.username,
            password=form_data.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/forgot-password")
async def forgot_password_endpoint(request: ForgotPasswordRequest):
    try:
        return await forgot_password(request.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
async def reset_password_endpoint(request: ResetPasswordRequest):
    try:
        return await reset_password(request.token, request.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))