import os

TELEGRAM_GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")
if not TELEGRAM_GROUP_ID:
    raise ValueError("No TELEGRAM_GROUP_ID found in environment variables")

# Get Telegram Bot Token from environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# Webhook URL path (should be difficult to guess)
WEBHOOK_URL_PATH = f"/webhook/{BOT_TOKEN}"

# Configure allowed commands
COMMANDS = {
    'start': 'Start the bot',
    'help': 'Get help information',
    'status': 'Check bot status',
    'info': 'Get information about the bot'
}

# Paystack secret key - MUST now be set in Replit as 'PAYSTACK_SECRET_KEY'
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")
if not PAYSTACK_SECRET_KEY:
    raise ValueError("No PAYSTACK_SECRET_KEY found in environment variables")

# Optional: print preview for debugging (don't do this in production!)
print(f"PAYSTACK_SECRET_KEY length: {len(PAYSTACK_SECRET_KEY)}")
print(f"PAYSTACK_SECRET_KEY preview: {PAYSTACK_SECRET_KEY[:10]}...")

# Telegram invite link - use env or default
TELEGRAM_INVITE_LINK = os.environ.get("TELEGRAM_INVITE_LINK",
                                      "https://t.me/+IqItzc6RRcVmNDdk")

# Admin user IDs - expects a comma-separated string of integers
ADMIN_USER_IDS = [
    int(id) for id in os.environ.get("ADMIN_USER_IDS", "").split(",")
    if id.strip().isdigit()
]

# Optional: print debug info
print("Loaded config:")
print(f"- BOT_TOKEN: {'*' * len(BOT_TOKEN)} (hidden)")
print(f"- TELEGRAM_INVITE_LINK: {TELEGRAM_INVITE_LINK}")
print(f"- ADMIN_USER_IDS: {ADMIN_USER_IDS}")
