import os
from datetime import datetime, timezone

from bson import ObjectId
from passlib.context import CryptContext

from backend.app.db.database import users_collection, password_reset_tokens_collection
from backend.app.schemas.user_schema import UserResponse
from backend.app.services.email_service import send_reset_link
from backend.app.services.jwt_service import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def register_user(username: str, email: str, password: str):
    existing_user = await users_collection.find_one(
        {"$or": [{"username": username}, {"email": email}]}
    )

    if existing_user:
        raise ValueError("User already exists")

    user_dict = {
        "username": username,
        "email": email,
        "password": hash_password(password),
        "isADMIN": False,
    }

    result = await users_collection.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)

    return UserResponse(**user_dict)


async def login_user(username: str, password: str):
    user = await users_collection.find_one({"username": username})

    if not user:
        raise ValueError("Invalid username or password")

    user["_id"] = str(user["_id"])

    is_valid = verify_password(password, user["password"])

    if not is_valid:
        raise ValueError("Invalid username or password")

    token = create_access_token(user_id=user["_id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(**user),
    }


async def forgot_password(email: str):
    
    user = await users_collection.find_one({"email": email})
    
    if not user:
        return {
            "message": "If an account with that email exists, a reset link has been sent."
        }

    user_id = str(user["_id"])

    await password_reset_tokens_collection.update_many(
        {"user_id": user_id, "used": False},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}},
    )

    token, jti = create_password_reset_token(user_id)
    now = datetime.now(timezone.utc)

    payload = decode_password_reset_token(token)

    reset_doc = {
        "user_id": user_id,
        "token_jti": jti,
        "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        "used": False,
        "created_at": now,
        "used_at": None,
    }

    await password_reset_tokens_collection.insert_one(reset_doc)

    frontend_url = os.getenv("FRONTEND_URL", "https://main.d2oqwmp8m9aqey.amplifyapp.com")
    reset_link = f"{frontend_url}/reset-password?token={token}"

    email_result = await send_reset_link(email, reset_link)
    print(email_result)

    if email_result != "success":

        raise ValueError(f"Failed to send reset email: {email_result}")

    return {
        "message": "If an account with that email exists, a reset link has been sent."
    }


async def reset_password(token: str, new_password: str):
    print("RESET PASSWORD CALLED")
    print("TOKEN:", token)
    print("NEW PASSWORD:", new_password)

    payload = decode_password_reset_token(token)
    print("PAYLOAD:", payload)

    user_id = payload["sub"]
    jti = payload["jti"]

    reset_record = await password_reset_tokens_collection.find_one(
        {
            "user_id": user_id,
            "token_jti": jti,
            "used": False,
        }
    )
    print("RESET RECORD:", reset_record)

    if not reset_record:
        raise ValueError("Invalid or already used reset token")

    now = datetime.now(timezone.utc)

    expires_at = reset_record["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        raise ValueError("Reset token has expired")

    try:
        oid = ObjectId(user_id)
    except Exception:
        raise ValueError("Invalid user id in token")

    user = await users_collection.find_one({"_id": oid})
    print("USER FOUND:", user)

    if not user:
        raise ValueError("User not found")

    new_hashed_password = hash_password(new_password)
    print("NEW HASH:", new_hashed_password)

    result = await users_collection.update_one(
        {"_id": oid},
        {"$set": {"password": new_hashed_password}},
    )
    print("UPDATE RESULT matched:", result.matched_count, "modified:", result.modified_count)

    await password_reset_tokens_collection.update_one(
        {"_id": reset_record["_id"]},
        {
            "$set": {
                "used": True,
                "used_at": now,
            }
        },
    )

    return {"message": "Password has been reset successfully"}