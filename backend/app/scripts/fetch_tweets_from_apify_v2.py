import os
import asyncio
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from apify_client import ApifyClient

from app.db.database import (
    connect_to_mongo,
    working_collection,
)

# --------------------------------------------------
# Load env
# --------------------------------------------------
env_path = Path(__file__).resolve().parent.parent.parent / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
ACTOR_ID = "apidojo/tweet-scraper"


# --------------------------------------------------
# Helper: parse Twitter / ISO dates safely
# --------------------------------------------------
def parse_created_at(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")


async def fetch_and_store_tweets():
    await connect_to_mongo()

    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN is missing from environment variables")

    client = ApifyClient(APIFY_API_TOKEN)

    run_input = {
    "searchTerms": [
        # ---------------- CORE ENTITY ----------------
        "(EAPC OR \"Eilat Ashkelon Pipeline\" OR KATZA) AND (Israel OR Ashkelon OR Eilat)",

        # ---------------- LEAK / FAILURE ----------------
        "(EAPC OR \"oil pipeline\" OR \"fuel pipeline\") AND (leak OR oil spill OR fuel leak OR contamination) AND (Israel OR Ashkelon OR Eilat)",

        "(pipeline OR oil pipeline OR fuel line) AND (rupture OR leak OR failure OR explosion) AND (EAPC OR Israel OR Ashkelon OR Eilat)",

        # ---------------- FIRE / EXPLOSION ----------------
        "(EAPC OR fuel terminal OR oil terminal) AND (fire OR explosion OR blaze) AND (Israel OR Ashkelon OR Eilat)",

        "(oil facility OR fuel storage OR industrial site) AND (fire OR explosion OR damage) AND (Ashkelon OR Eilat OR Israel)",

        # ---------------- INFRASTRUCTURE ----------------
        "(EAPC OR oil infrastructure OR fuel infrastructure) AND (facility OR terminal OR port) AND (Israel OR Ashkelon OR Eilat)",

        "(fuel terminal OR oil terminal OR storage facility) AND (failure OR damage OR incident) AND (Ashkelon OR Eilat OR Israel)",

        # ---------------- ENVIRONMENT ----------------
        "(oil spill OR fuel spill OR marine pollution) AND (EAPC OR Israel OR Eilat OR Ashkelon)",

        "(environmental damage OR pollution) AND (oil OR fuel) AND (Eilat OR Red Sea OR Israel)",

        # ---------------- HUMAN STYLE ----------------
        "oil spill Eilat Israel",
        "fuel leak Ashkelon Israel",
        "something happened at oil terminal Israel",
        "strong fuel smell Eilat",
        "fire at fuel facility Ashkelon Israel",
    ],

    "maxItems": 200,
    "sort": "Latest",
    "tweetLanguage": "en",

    # 🎯 last year
    "startDate": "2025-04-01",
    "endDate": "2026-04-14",
}
    print("🚀 Running Tweet Scraper actor...")
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    dataset_id = run["defaultDatasetId"]

    items = client.dataset(dataset_id).list_items().items
    print(f"📥 Pulled {len(items)} tweets")

    working_docs = []

    for item in items:
        text = item.get("text")
        created_at = item.get("createdAt")

        if not text or not created_at:
            continue

        created_at_dt = parse_created_at(created_at)

        doc = {
            "uploaded_by": "apify",
            "content": text,
            "created_at": created_at_dt,
            "status": "pending",
            "locked_at": None,
            "locked_by": None,
            "tagged_by": None,
            "tagged_at": None,
            "is_dangerous": None,
            "category": None,
        }

        working_docs.append(doc)

    if not working_docs:
        print("⚠️ No valid tweets found in Apify response")
        return

    result = await working_collection.insert_many(working_docs)
    print(f"✅ Inserted {len(result.inserted_ids)} tweets into working")


if __name__ == "__main__":
    asyncio.run(fetch_and_store_tweets())