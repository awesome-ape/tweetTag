import asyncio
from datetime import datetime, timezone
from app.db.database import working_collection, connect_to_mongo,close_mongo_connection

async def create_sample_tweet(content: str):


    new_tweet = {
        "content": content,
        "created_at": datetime.now(timezone.utc)
    }

    try:
        result = await working_collection.insert_one(new_tweet)
        print(f"✅ New tweet created with id: {result.inserted_id}")
    except Exception as e:
        print("❌ An error occurred:", e)

async def  run_seed():
    connect_to_mongo()
    await create_sample_tweet("Hello, this is a sample tweet!")
    await create_sample_tweet("poopa")
    await create_sample_tweet("poopa floopa")
    await create_sample_tweet("floopa poopa!!!!!!!")
    close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_seed())
    