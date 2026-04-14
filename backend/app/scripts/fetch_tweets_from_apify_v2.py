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
        # ---------------- DIRECT EVENT ----------------
        "(Rutenberg OR \"Rutenberg power station\" OR \"power plant Ashkelon\") AND (collapse OR collapsed OR structural failure)",

        "(coal pier OR pier OR jetty) AND (collapse OR collapsed) AND (Rutenberg OR Ashkelon OR Israel)",

        "(crane OR gantry crane) AND (collapsed OR collapse) AND (Rutenberg OR Ashkelon OR Israel)",


        # ---------------- WEATHER CONTEXT ----------------
        "(strong winds OR storm OR severe weather) AND (crane OR pier OR power plant) AND (Ashkelon OR Israel)",

        "(storm OR high winds) AND (crane collapse OR pier collapse) AND (Rutenberg OR Ashkelon OR Israel)",


        # ---------------- CASUALTIES / RESCUE ----------------
        "(Rutenberg OR coal pier OR Ashkelon) AND (missing OR rescued OR injured OR casualties)",

        "(worker OR workers) AND (missing OR rescued OR killed OR injured) AND (Rutenberg OR Ashkelon OR Israel)",

        "(body found OR remains found) AND (Rutenberg OR coal pier OR crane OR Ashkelon)",


        # ---------------- ELECTRICITY / INFRASTRUCTURE ----------------
        "(power plant OR Israel Electric Corporation) AND (collapse OR accident OR incident) AND (Rutenberg OR Ashkelon OR Israel)",

        "(energy infrastructure OR industrial facility) AND (collapse OR damage OR accident) AND (Rutenberg OR Ashkelon OR Israel)",


        # ---------------- HUMAN STYLE ----------------
        "crane collapse Ashkelon power plant",
        "pier collapse Ashkelon",
        "coal pier collapse Israel",
        "accident at power plant Ashkelon",
        "workers missing Ashkelon power plant",
        "crane fell Ashkelon",
    ],

    "maxItems": 300,
    "sort": "Latest",
    "tweetLanguage": "en",

    # 🎯 March 2023 with buffer
    "startDate": "2023-03-01",
    "endDate": "2023-05-01",
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