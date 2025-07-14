# telegram_invite.py

import requests
import time
from config import BOT_TOKEN, TELEGRAM_GROUP_ID

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def generate_invite_link():
    #expire_date = int(time.time()) + 5 * 60  # 5 minutes from now
    """Generate a new invite link for the Telegram group/channel with expiry and member limit"""
    url = f"{TELEGRAM_API_URL}/createChatInviteLink"
    payload = {
        "chat_id": TELEGRAM_GROUP_ID,
        # "expire_date": expire_date,
        # "member_limit": 30,  # Only 30 user can join using this link
        "creates_join_request": True  # This enables admin approval
    }
    response = requests.post(url, json=payload)
    result = response.json()

    if result.get("ok"):
        return result["result"]["invite_link"]
    else:
        print("Error while generating invite link:", result)  # For debugging
        raise Exception(f"Failed to generate invite link: {result}")
