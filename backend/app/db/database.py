import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path


# Load environment variables from .env file
base_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")

#the connection object
client = AsyncIOMotorClient(os.getenv("MONGO_URI"))

#db refers to the spacific database in the cluster
db = client.tweet_tag_database
# uses ping to make sure the client was created seccessfully
async def connect_to_mongo():
    try:
        await client.admin.command('ping')
        print("✅ MongoDB connected successfully.")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise e

async def close_mongo_connection():
    print("Closing MongoDB connection...")
    client.close()

backup_collection = db.get_collection("backup")
escalation_collection = db.get_collection("escalation")
working_collection = db.get_collection("working")
processed_collection = db.get_collection("processed")
user_collection = db.get_collection("users")