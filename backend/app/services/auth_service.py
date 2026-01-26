from passlib.context import CryptContext
from app.db.database import users_collection
from app.schemas.user_schema import UserSchema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def register_user(username: str, email: str, password: str):
    existing_user = await users_collection.find_one({
        "$or": [
            {"username": username},
            {"email": email}
        ]
    })

    if existing_user:
        raise ValueError("User already exists")

    hashed_password = hash_password(password)

    user_dict = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "isADMIN": False
    }

    result = await users_collection.insert_one(user_dict)

    user_dict["_id"] = str(result.inserted_id)

    return UserSchema(**user_dict)
