

from bson import ObjectId
from app.db.database import users_collection

async def is_admin(user_id: str) -> bool:
    # i add the imports inside the function so i acn import this function anywhere without causing circular imports
    from bson import ObjectId
    from app.db.database import users_collection
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return False
    return user["isADMIN"] is not None