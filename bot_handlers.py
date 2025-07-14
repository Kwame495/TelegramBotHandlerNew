import logging
import json
import requests
from config import BOT_TOKEN, COMMANDS, ADMIN_USER_IDS

# Set up logger
logger = logging.getLogger(__name__)


def send_telegram_message(chat_id, text, parse_mode=None, reply_markup=None):
    """Send a message to Telegram chat"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {"chat_id": chat_id, "text": text}

        if parse_mode:
            data['parse_mode'] = parse_mode

        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)

        response = requests.post(url, json=data)

        # Print and log the raw Telegram API response
        logger.debug(f"Telegram API response status: {response.status_code}")
        logger.debug(f"Telegram API response body: {response.text}")
        print(f"Telegram API response status: {response.status_code}")
        print(f"Telegram API response body: {response.text}")

        if response.status_code == 200 and response.json().get('ok'):
            logger.debug(f"Message sent successfully to chat {chat_id}")
            return response.json()
        else:
            logger.error(
                f"Failed to send message to chat {chat_id}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception while sending message to chat {chat_id}: {e}")
        print(f"Exception while sending message to chat {chat_id}: {e}")
        return None


def extract_command(text):
    """Extract command and arguments from message text"""
    if not text:
        return None, None

    parts = text.strip().split(' ', 1)

    command_part = parts[0].split('@')[0].lower()
    if not command_part.startswith('/'):
        return None, None
    command = command_part[1:]

    args = parts[1] if len(parts) > 1 else ''
    return command, args


def process_update(update):
    """Process incoming update from Telegram"""
    try:
        if 'message' in update:
            return process_message(update['message'])
        elif 'callback_query' in update:
            return process_callback_query(update['callback_query'])
        else:
            logger.info(f"Received unhandled update type: {update}")
            return None
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return None


def process_message(message):
    """Process incoming message"""
    try:
        chat_id = message.get('chat', {}).get('id')
        user_id = message.get('from', {}).get('id')

        if not chat_id:
            logger.error("No chat ID found in message")
            return None

        text = message.get('text', '')

        if text:
            command, args = extract_command(text)

            if command:
                return handle_command(command, args, chat_id, user_id, message)
            else:
                return handle_regular_message(text, chat_id, user_id, message)

        if any(key in message for key in
               ['photo', 'document', 'audio', 'video', 'voice', 'sticker']):
            return handle_media_message(message, chat_id, user_id)

        return None
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return None


def handle_command(command, args, chat_id, user_id, message):
    """Handle commands received from users"""
    try:
        if command in COMMANDS:
            logger.info(f"Received command /{command} from user {user_id}")

            # Example admin command check (add broadcast to COMMANDS if you want)
            if command == 'broadcast' and user_id not in ADMIN_USER_IDS:
                send_telegram_message(
                    chat_id,
                    "Sorry, this command is only available to administrators.")
                return None

            if command == 'start':
                return cmd_start(chat_id, user_id, message)
            elif command == 'help':
                return cmd_help(chat_id, user_id, message)
            elif command == 'status':
                return cmd_status(chat_id, user_id, message)
            elif command == 'info':
                return cmd_info(chat_id, user_id, message)
            else:
                send_telegram_message(
                    chat_id,
                    f"The command /{command} is recognized but not yet implemented."
                )
                return None
        else:
            send_telegram_message(
                chat_id,
                f"Sorry, I don't recognize the command /{command}. Type /help to see available commands."
            )
            return None
    except Exception as e:
        logger.error(f"Error handling command {command}: {e}")
        send_telegram_message(
            chat_id,
            f"Error processing command /{command}. Please try again later.")
        return None


def handle_regular_message(text, chat_id, user_id, message):
    """Handle regular text messages (not commands)"""
    logger.info(f"Received message from user {user_id}: {text[:20]}...")

    send_telegram_message(
        chat_id, "I received your message. Use /help to see what I can do.")
    return None


def handle_media_message(message, chat_id, user_id):
    """Handle media messages (photos, documents, etc.)"""
    media_type = None

    if 'photo' in message:
        media_type = "photo"
    elif 'document' in message:
        media_type = "document"
    elif 'audio' in message:
        media_type = "audio"
    elif 'video' in message:
        media_type = "video"
    elif 'voice' in message:
        media_type = "voice message"
    elif 'sticker' in message:
        media_type = "sticker"

    logger.info(f"Received {media_type} from user {user_id}")

    send_telegram_message(
        chat_id,
        f"I received your {media_type}, but I'm not designed to process media files yet."
    )
    return None


def process_callback_query(callback_query):
    """Process callback queries from inline keyboard buttons"""
    try:
        callback_data = callback_query.get('data')
        chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
        user_id = callback_query.get('from', {}).get('id')

        if not callback_data or not chat_id:
            logger.error("Missing data or chat_id in callback query")
            return None

        logger.info(
            f"Received callback query with data: {callback_data} from user {user_id}"
        )

        answer_callback_query(callback_query.get('id'))

        send_telegram_message(chat_id, f"You selected: {callback_data}")

        return None
    except Exception as e:
        logger.error(f"Error processing callback query: {e}")
        return None


def answer_callback_query(callback_query_id, text=None, show_alert=False):
    """Answer a callback query to remove the loading indicator"""
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery'

        data = {'callback_query_id': callback_query_id}

        if text:
            data['text'] = text

        if show_alert:
            data['show_alert'] = True

        response = requests.post(url, json=data)

        if response.status_code != 200 or not response.json().get('ok'):
            logger.error(f"Failed to answer callback query: {response.text}")
    except Exception as e:
        logger.error(f"Error answering callback query: {e}")


# Command handlers
def cmd_start(chat_id, user_id, message):
    user_name = message.get('from', {}).get('first_name', 'there')

    welcome_text = (f"Hello, {user_name}! 👋\n\n"
                    f"Welcome to the Telegram Bot. I'm here to assist you.\n\n"
                    f"Use /help to see available commands.")

    reply_markup = {
        'keyboard': [['/help', '/status'], ['/info']],
        'resize_keyboard': True
    }

    send_telegram_message(chat_id, welcome_text, reply_markup=reply_markup)


def cmd_help(chat_id, user_id, message):
    help_text = "Here are the commands you can use:\n\n"

    for cmd, description in COMMANDS.items():
        help_text += f"/{cmd} - {description}\n"

    send_telegram_message(chat_id, help_text)


def cmd_status(chat_id, user_id, message):
    status_text = (
        "✅ Bot Status: Operational\n\n"
        "The bot is running normally and ready to process your commands.")

    send_telegram_message(chat_id, status_text)


def cmd_info(chat_id, user_id, message):
    info_text = (
        "📱 *Telegram Webhook Bot*\n\n"
        "This bot demonstrates how to create a webhook-based Telegram bot using Flask.\n\n"
        "Features:\n"
        "• Processes incoming messages\n"
        "• Handles commands\n"
        "• Responds to user interactions\n\n"
        "Use /help to see available commands.")

    send_telegram_message(chat_id, info_text, parse_mode="Markdown")
