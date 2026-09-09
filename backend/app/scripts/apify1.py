import os
import smtplib
from email.mime.text import MIMEText

from backend.app.db.database import db, users_collection


async def send_tagging_reminders_to_all_users():
    email_from = os.getenv("EMAIL_FROM")
    password = os.getenv("APP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT"))

    processed_collection = db.get_collection("processed")

    site_url = "https://main.d2oqwmp8m9aqey.amplifyapp.com"
    target = 800

    sent_count = 0
    failed_count = 0
    skipped_admin_count = 0

    users_cursor = users_collection.find({})

    async for user in users_cursor:
        # ❌ skip admins
        if user.get("isADMIN") is True:
            skipped_admin_count += 1
            print(f"Skipping admin: {user.get('username')}")
            continue

        user_id = str(user["_id"])
        username = user.get("username", "user")
        email = user.get("email")

        if not email:
            print(f"Skipping {username}: no email")
            continue

        tagged_count = await processed_collection.count_documents({
            "tagged_by": user_id
        })

        remaining = max(0, target - tagged_count)

        subject = f"Only {remaining} tweets left to tag 🚀"

        body = f"""Hi {username},

You've already tagged {tagged_count} tweets — great job!

You're only {remaining} tweets away from reaching your goal of {target}.

Ready to continue?

👉 {site_url}

Happy tagging 💛  
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
            print(f"✅ Sent to {username} ({email}) | tagged={tagged_count}")

        except Exception as e:
            failed_count += 1
            print(f"❌ Failed sending to {username} ({email}): {e}")

    return {
        "message": "Finished sending reminders",
        "sent_count": sent_count,
        "failed_count": failed_count,
        "skipped_admin_count": skipped_admin_count,
    }


# להרצה כקובץ עצמאי
if __name__ == "__main__":
    import asyncio

    asyncio.run(send_tagging_reminders_to_all_users())
