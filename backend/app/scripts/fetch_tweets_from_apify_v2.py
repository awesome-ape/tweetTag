import os
import asyncio
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from apify_client import ApifyClient

from app.db.database import (
    connect_to_mongo,
    backup_collection,
    working_collection,
)

# --------------------------------------------------
# Load env
# --------------------------------------------------
# This first line handles local dev (looking for the file)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"

if env_path.exists():
    # Local: Use your file
    load_dotenv(dotenv_path=env_path)
else:
    # AWS: Use the variables from the Console
    load_dotenv()

# This second line is the safety net for AWS
# If the file above didn't exist, this ensures we grab the AWS Console variables
load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
ACTOR_ID = "apidojo/tweet-scraper"

# --------------------------------------------------
# Indicative keywords
# --------------------------------------------------
SEARCH_TERMS = [
    "oil refinery",
    "gas platform",
    "energy infrastructure",
    "power plant",
    "electric grid",
    "natural gas",
    "pipeline",
]

MAX_ITEMS = 10


# --------------------------------------------------
# Helper: parse Twitter / ISO dates safely
# --------------------------------------------------
def parse_created_at(date_str: str) -> datetime:
    """
    Handles both:
    - ISO format: 2026-02-01T22:04:24Z
    - Twitter format: Sun Feb 01 22:04:24 +0000 2026
    """
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")


async def fetch_and_store_tweets():
    await connect_to_mongo()

    client = ApifyClient(APIFY_API_TOKEN)

    run_input = {
        "searchTerms": SEARCH_TERMS,
        "maxItems": MAX_ITEMS,
        "sort": "Latest",
        "tweetLanguage": "en",
    }

    print("🚀 Running Tweet Scraper actor...")
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    dataset_id = run["defaultDatasetId"]

    items = client.dataset(dataset_id).list_items().items
    print(f"📥 Pulled {len(items)} tweets")

    backup_docs = []
    working_docs = []

    for item in items:
        text = item.get("text")
        created_at = item.get("createdAt")

        if not text or not created_at:
            continue

        created_at_dt = parse_created_at(created_at)

        base_doc = {
            "uploaded_by": "apify",
            "content": text,
            "created_at": created_at_dt,
            "status": "pending",
            "locked_at": None,
            "tagged_by": None,
            "is_dangerous": None,
            "category": None,
        }

        backup_docs.append(
            {
                **base_doc,
                "raw": item,
            }
        )

        working_docs.append(base_doc)

    if working_docs:
        await backup_collection.insert_many(backup_docs)
        await working_collection.insert_many(working_docs)

    print(f"✅ Inserted {len(working_docs)} tweets to working & backup collections")


if __name__ == "__main__":
    asyncio.run(fetch_and_store_tweets())
