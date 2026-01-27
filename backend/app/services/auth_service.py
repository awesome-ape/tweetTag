from passlib.context import CryptContext
from app.db.database import users_collection
from app.schemas.user_schema import UserInDB, UserResponse
from app.services.jwt_service import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def register_user(username: str, email: str, password: str):
    existing_user = await users_collection.find_one({
        "$or": [{"username": username}, {"email": email}]
    })

    if existing_user:
        raise ValueError("User already exists")

    user_dict = {
        "username": username,
        "email": email,
        "password": hash_password(password),
        "isADMIN": False
    }

    result = await users_collection.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)

    return UserResponse(**user_dict)


async def login_user(username: str, password: str):
    user = await users_collection.find_one({"username": username})

    print("USER FROM DB:", user)
    print("PLAIN PASSWORD:", password)

    if not user:
        print("❌ user not found")
        raise ValueError("Invalid username or password")

    user["_id"] = str(user["_id"])

    is_valid = verify_password(password, user["password"])
    print("PASSWORD MATCH:", is_valid)

    if not is_valid:
        raise ValueError("Invalid username or password")

    token = create_access_token(user_id=user["_id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }

