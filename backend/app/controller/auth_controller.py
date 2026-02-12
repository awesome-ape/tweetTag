from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# Add 'backend.' here to match the project root path
from backend.app.services.auth_service import register_user, login_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


@router.post("/register")
async def register(request: RegisterRequest):
    try:
        return await register_user(request.username, request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    # request: LoginRequest,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    try:
        return await login_user(
            # request.username,
            # request.password
            username=form_data.username,
            password=form_data.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
