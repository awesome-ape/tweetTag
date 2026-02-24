from bson import ObjectId
from backend.app.db.database import users_collection


async def is_admin(user_id: str) -> bool:
    """
    Returns True only if user exists AND isADMIN == True
    """

    try:
        oid = ObjectId(str(user_id))
    except Exception:
        return False

    user = await users_collection.find_one({"_id": oid})

    if not user:
        return False

    # ⚠️ התיקון הקריטי כאן
    return bool(user.get("isADMIN", False))


async def get_user_by_id(user_id: str) -> str | None:
    """
    Returns username string or None.
    """

    try:
        oid = ObjectId(str(user_id))
    except Exception:
        return None

    user = await users_collection.find_one(
        {"_id": oid},
        {"username": 1}
    )

    if not user:
        return None

    return user.get("username")