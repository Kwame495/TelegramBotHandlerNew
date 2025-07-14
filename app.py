import os
import logging
import hmac
import hashlib
import sqlite3
import bot_handlers  # ✅ Import here so it's always in scope
from datetime import datetime
from flask import Flask, request, jsonify, render_template, abort
import requests
from bot_handlers import process_update, send_telegram_message, handle_command, handle_regular_message
from config import BOT_TOKEN, WEBHOOK_URL_PATH, PAYSTACK_SECRET_KEY, TELEGRAM_INVITE_LINK
from telegram_invite import generate_invite_link

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SESSION_SECRET")

DB_PATH = 'payments.db'


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE,
                status TEXT,
                amount INTEGER,
                email TEXT,
                full_name TEXT,
                paid_at TEXT,
                chat_id TEXT,
                invite_link TEXT
            )
        ''')
        conn.commit()


def save_payment(data, invite_link=None):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # Extract full_name and chat_id from metadata.custom_fields
        full_name = None
        chat_id = None
        for field in data.get('metadata', {}).get('custom_fields', []):
            if field.get('variable_name') == 'full_name':
                full_name = field.get('value')
            elif field.get('variable_name') == 'chat_id':
                chat_id = field.get('value')

        try:
            c.execute(
                '''
                INSERT INTO payments (reference, status, amount, email, full_name, paid_at, chat_id, invite_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data['reference'], data['status'], data['amount'],
                      data['customer']['email'], full_name, data['paid_at'],
                      chat_id, invite_link))
            conn.commit()
        except sqlite3.IntegrityError:
            logger.warning(
                f"Payment with reference {data['reference']} already saved")


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@app.route('/all_payments', methods=['GET'])
def all_payments():
    # Read optional limit and offset query params (default: all records)
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        c = conn.cursor()

        base_query = """
            SELECT id, reference, status, amount, email, full_name, paid_at, chat_id, invite_link
            FROM payments
            ORDER BY id DESC
        """

        # Add pagination if limit is specified
        if limit is not None:
            base_query += " LIMIT ? OFFSET ?"
            c.execute(base_query, (limit, offset))
        else:
            c.execute(base_query)

        payments = c.fetchall()

        # Format paid_at field (if exists)
        for payment in payments:
            paid_at = payment.get("paid_at")
            if paid_at:
                try:
                    payment["paid_at"] = datetime.strptime(
                        paid_at,
                        "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y %I:%M %p")
                except Exception:
                    pass  # leave as is if format doesn't match

        return jsonify({'payments': payments})


@app.route('/dashboard_payments')
def dashboard_payments():
    return render_template('dashboard_payments.html')


init_db()

if PAYSTACK_SECRET_KEY is None:
    raise ValueError("PAYSTACK_SECRET_KEY not set in environment variables")


def verify_paystack_signature(request):
    signature = request.headers.get('X-Paystack-Signature')
    if signature is None:
        abort(400, "Missing signature")

    # Get raw request body bytes exactly as sent
    body = request.get_data()

    # Use your secret key exactly as configured in Paystack
    secret_key = PAYSTACK_SECRET_KEY.encode('utf-8')

    computed_signature = hmac.new(secret_key, body, hashlib.sha512).hexdigest()

    print(f"Received signature: {signature}")
    print(f"Computed signature: {computed_signature}")

    if not hmac.compare_digest(computed_signature, signature):
        abort(400, "Invalid signature")

    return True


@app.route('/payment_webhook', methods=['POST'])
def payment_webhook():
    try:
        if not verify_paystack_signature(request):
            logger.warning("Invalid Paystack webhook signature")
            abort(400, "Invalid signature")

        payload = request.json
        if payload is None:
            return jsonify({
                'status': 'error',
                'message': 'Invalid JSON payload'
            }), 400

        logger.debug(f"Payment webhook payload: {payload}")
        event = payload.get('event')
        data = payload.get('data', {})

        if event == 'charge.success':
            reference = data.get('reference')
            if not reference:
                logger.warning("No reference found in payment data")
                return jsonify({
                    'status': 'error',
                    'message': 'No reference found'
                }), 400

            # ✅ Extract chat_id before checking duplicates
            metadata = data.get('metadata', {})
            chat_id = None
            for field in metadata.get('custom_fields', []):
                if field.get('variable_name') == 'chat_id':
                    chat_id = field.get('value')
                    break

            # ✅ Check if reference already exists in DB
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT 1 FROM payments WHERE reference = ?",
                          (reference, ))
                exists = c.fetchone()

            if exists:
                logger.info(
                    f"Duplicate webhook ignored for reference: {reference}")
                # Optionally send a reminder if chat_id is known
                if chat_id:
                    send_telegram_message(
                        chat_id,
                        "✅ We already received your payment. If you need your invite link again, please contact support."
                    )
                return jsonify({
                    'status': 'ignored',
                    'message': 'Duplicate reference'
                }), 200

            # ✅ Generate invite link and send to user
            invite_link = None
            if chat_id:
                try:
                    invite_link = generate_invite_link(
                    )  # This uses your updated telegram_invite.py function
                    message = f"🎉 Thank you for your payment of ₵{data['amount'] / 100:.2f}!\nHere is your invite link (valid for 5 minutes, single use):\n{invite_link}"
                except Exception as e:
                    logger.error(f"Failed to generate invite link: {e}")
                    message = "✅ Payment received! But we couldn’t generate your invite link. Please contact support."

                send_telegram_message(chat_id, message)
                logger.info(f"Sent invite message to chat_id {chat_id}")
            else:
                logger.warning("No chat_id found in payment metadata")

            # ✅ Save payment to DB (with invite link)
            save_payment(data, invite_link)

        return jsonify({'status': 'success'})

    except Exception as e:
        logger.error(f"Error processing payment webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/pay')
def payment_form():
    """Serve payment form page"""
    return render_template('payment_form.html')


@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        print("Received update:", update)
        logger.debug(f"Received update: {update}")
        process_update(update)
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    try:
        base_url = f"https://{request.host}"
        webhook_url = f"{base_url}{WEBHOOK_URL_PATH}"

        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook',
            json={'url': webhook_url})

        response_json = response.json()
        if response.status_code == 200 and response_json.get('ok'):
            return jsonify({
                'status': 'success',
                'message': f'Webhook set to: {webhook_url}',
                'telegram_response': response_json
            })
        else:
            return jsonify({
                'status': 'error',
                'message':
                f"Failed to set webhook: {response_json.get('description', 'Unknown error')}",
                'telegram_response': response_json
            }), 400
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    try:
        response = requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo')
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'webhook_info': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get webhook info',
                'telegram_response': response.json()
            }), 500
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    try:
        response = requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook')
        if response.status_code == 200 and response.json().get('ok'):
            return jsonify({
                'status': 'success',
                'message': 'Webhook deleted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to delete webhook',
                'telegram_response': response.json()
            }), 500
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/test_bot', methods=['POST'])
def test_bot():
    data: dict = request.get_json()  # Add type hint

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        chat_id = data.get('chat_id', '123456789')
        message_text = data.get('message', '')

        if not message_text:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400

        logger.info(f"Testing bot with message: {message_text}")

        simulated_message = {
            'message_id': 1,
            'from': {
                'id': int(chat_id),
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser'
            },
            'chat': {
                'id': int(chat_id),
                'type': 'private',
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser'
            },
            'date': int(datetime.now().timestamp()),
            'text': message_text
        }

        response_tracking = {'text': None, 'sent': False}

        def test_send_telegram_message(chat_id,
                                       text,
                                       parse_mode=None,
                                       reply_markup=None):
            response_tracking['text'] = text
            response_tracking['parse_mode'] = parse_mode
            response_tracking['reply_markup'] = reply_markup
            response_tracking['sent'] = True
            logger.info(f"Would send to Telegram: {text[:50]}...")
            return {'ok': True, 'result': {'message_id': 1}}

        original_send = send_telegram_message

        try:
            bot_handlers.send_telegram_message = test_send_telegram_message

            if message_text.startswith('/'):
                command, args = bot_handlers.extract_command(message_text)
                if command:
                    handle_command(command, args, int(chat_id), int(chat_id),
                                   simulated_message)
                else:
                    handle_regular_message(message_text, int(chat_id),
                                           int(chat_id), simulated_message)
            else:
                handle_regular_message(message_text, int(chat_id),
                                       int(chat_id), simulated_message)

        finally:
            bot_handlers.send_telegram_message = original_send  # ✅ No more Pyright error

        if response_tracking['sent']:
            return jsonify({
                'status': 'success',
                'message': 'Message processed successfully',
                'response': {
                    'text': response_tracking['text'],
                    'parse_mode': response_tracking['parse_mode'],
                    'has_reply_markup': bool(response_tracking['reply_markup'])
                }
            })
        else:
            return jsonify({
                'status':
                'warning',
                'message':
                'Message processed but no response was generated'
            })

    except Exception as e:
        logger.error(f"Error testing bot: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
