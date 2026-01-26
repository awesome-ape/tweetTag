import asyncio
from app.db.database import users_collection, connect_to_mongo

async def create_first_user(username: str):
    # Ensure DB is connected
    await connect_to_mongo()
    
    new_user = {
        "username": username,
        "email": "poopa@poopamail.com",
        "isADMIN": False,
        "password": "Poopa1234"
    }

    try:
        existing_user = await users_collection.find_one({"username": username})
        if existing_user:
            print(f"⚠️ User '{username}' already exists.")
        else:
            result = await users_collection.insert_one(new_user)
            print(f"✅ New user created with id: {result.inserted_id}")
    except Exception as e:
        print("❌ An error occurred:", e)

# This must be at the VERY LEFT (no indentation)
if __name__ == "__main__":
    # We pass the username we want to create here
    asyncio.run(create_first_user("PoopaUser44"))