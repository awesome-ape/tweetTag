import asyncio
from datetime import datetime, timezone
from backend.app.db.database import (
    working_collection,
    connect_to_mongo,
    close_mongo_connection,
)


async def create_sample_tweet(content: str):

    new_tweet = {
        "content": content,
        "created_at": datetime.now(timezone.utc),
        "status": "pending",
        "uploaded_by": "charli",
    }
    new_tweet_in_db = {
        **new_tweet,
        "tagged_by": None,
        "is_dangerous": None,
        "category": None,
    }

    try:
        result = await working_collection.insert_one(new_tweet_in_db)
        print(f"✅ New tweet created with id: {result.inserted_id}")
    except Exception as e:
        print("❌ An error occurred:", e)


async def run_seed():
    connect_to_mongo()
    await create_sample_tweet("Hello, this is a sample tweet!")
    await create_sample_tweet("poopa")
    await create_sample_tweet("poopa floopa")
    await create_sample_tweet("floopa poopa!!!!!!!")
    await create_sample_tweet("pooper!!!!!!!")
    await create_sample_tweet("pooper flooper!!!!!!!")
    await create_sample_tweet("poopon")
    await create_sample_tweet("poopon floopon")
    await create_sample_tweet("mr pooper")
    await create_sample_tweet("mr flooper")
    await create_sample_tweet("mr poopon")
    await create_sample_tweet("mr floopon")
    await create_sample_tweet("mr pooper flooper")
    close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(run_seed())
