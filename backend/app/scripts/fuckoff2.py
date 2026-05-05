import os
import smtplib
from email.mime.text import MIMEText
import asyncio

from backend.app.db.database import users_collection
from backend.app.services.tweets.display import get_daily_tagging_stats


async def send_daily_ranking_emails():
    email_from = os.getenv("EMAIL_FROM")
    password = os.getenv("APP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT"))

    site_url = "https://main.d2oqwmp8m9aqey.amplifyapp.com"

    daily_stats = await get_daily_tagging_stats()

    if not daily_stats:
        print("❌ No daily stats found")
        return

    latest_date = sorted(daily_stats.keys(), reverse=True)[0]
    today_users = daily_stats[latest_date]

    sorted_users = sorted(today_users, key=lambda x: x["count"], reverse=True)

    ranking_map = {}
    for i, user in enumerate(sorted_users, start=1):
        ranking_map[user["username"]] = {
            "rank": i,
            "count": user["count"],
        }

    total_users_today = len(sorted_users)

    top_3_lines = []
    medals = ["🥇", "🥈", "🥉"]

    for index, row in enumerate(sorted_users[:3]):
        top_3_lines.append(
            f"{medals[index]} #{index + 1}: {row['username']} — {row['count']} tweets"
        )

    top_3_text = "\n".join(top_3_lines) if top_3_lines else "No rankings yet today."

    sent_count = 0
    skipped_admin_count = 0
    skipped_no_email_count = 0
    skipped_not_active_today_count = 0

    users_cursor = users_collection.find({})

    async for user in users_cursor:
        if user.get("isADMIN"):
            skipped_admin_count += 1
            continue

        username = user.get("username")
        email = user.get("email")

        if not email:
            skipped_no_email_count += 1
            continue

        if username not in ranking_map:
            skipped_not_active_today_count += 1
            continue

        rank = ranking_map[username]["rank"]
        count = ranking_map[username]["count"]

        subject = f"10 minutes left — your ranking today is #{rank} 🏆"

        body = f"""Hi {username},

⏳ 10 minutes left!

Your current ranking today: #{rank} out of {total_users_today} users

You tagged {count} tweets today.

Today's top taggers:
{top_3_text}

Keep tagging here:
{site_url}

TweetTag Team 🐥
"""
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = email

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(email_from, password)
                server.send_message(msg)

            sent_count += 1
            print(f"✅ Sent to {username} | rank #{rank}")

        except Exception as e:
            print(f"❌ Failed for {username}: {e}")

    print(f"🎉 Done. Sent {sent_count} emails for {latest_date}")
    print(f"Skipped admins: {skipped_admin_count}")
    print(f"Skipped no email: {skipped_no_email_count}")
    print(f"Skipped not active today: {skipped_not_active_today_count}")


if __name__ == "__main__":
    asyncio.run(send_daily_ranking_emails())