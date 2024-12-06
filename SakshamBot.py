import logging
import datetime
import requests
import json
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Razorpay API credentials
razorpay_key = "rzp_live_0qzU8YekuoPLIT"
razorpay_secret = "6VzXh2mLnlr4WgdiSaiHJyYk"

# Define greetings based on time
def get_greeting():
    current_hour = datetime.datetime.now().hour
    if 0 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

# Global dictionary to store user states
user_states = {}

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    
    logger.info(f"Received message from {chat_id}: {msg['text']}")
    
    if content_type == 'text':
        command = msg['text'].strip()

        if chat_id not in user_states:
            user_states[chat_id] = None

        if command == '/start':
            user_first_name = msg['from']['first_name']
            greeting = get_greeting()
            welcome_message = f"{greeting}, {user_first_name}! I'm Siddhi, your assistant. How can I help you today?"
            bot.sendMessage(chat_id, welcome_message)
        
        elif command == '/help':
            help_message = (
                "Available commands:\n"
                "/start - Start the bot and get a greeting\n"
                "/help - Show this help message\n"
                "/pay - Generate a payment QR code\n"
                "/cancel - Cancel the current operation"
            )
            bot.sendMessage(chat_id, help_message)
        
        elif command == '/pay':
            bot.sendMessage(chat_id, "Please enter the amount you want to pay (in INR):")
            user_states[chat_id] = 'awaiting_amount'
        
        elif user_states[chat_id] == 'awaiting_amount':
            if command.isdigit():
                try:
                    amount = int(command) * 100  # Convert to paise
                    user_first_name = msg['from']['first_name']
                    headers = {
                        'Content-Type': 'application/json'
                    }
                    data = {
                        "amount": amount,
                        "currency": "INR",
                        "description": "Payment for services",
                        "customer": {
                            "name": user_first_name,
                            "contact": "9876543210"  # Ensure this is a valid contact number
                        },
                        "notify": {
                            "sms": False,
                            "email": False
                        },
                        "reminder_enable": False
                    }
                    logger.info(f"Sending payment link generation request with data: {data}")
                    response = requests.post(
                        'https://api.razorpay.com/v1/payment_links',
                        auth=(razorpay_key, razorpay_secret),
                        data=json.dumps(data),
                        headers=headers
                    )
                    logger.info(f"Received response: {response.status_code} - {response.text}")
                    if response.status_code == 200:
                        payment_data = response.json()
                        payment_link = payment_data.get('short_url', None)
                        payment_id = payment_data.get('id', None)
                        if payment_link:
                            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text='Pay', url=payment_link)]
                            ])
                            bot.sendMessage(chat_id, f"Here is your payment link, {user_first_name}:", reply_markup=keyboard)
                            user_states[chat_id] = payment_id  # Store the payment ID to check status later
                        else:
                            bot.sendMessage(chat_id, "Failed to retrieve payment link URL. Please try again later.")
                    else:
                        bot.sendMessage(chat_id, f"Failed to generate payment link. Server responded with: {response.text}")
                
                except Exception as e:
                    logger.error(f"Error generating payment link: {e}")
                    bot.sendMessage(chat_id, f"An error occurred while generating the payment link. Please try again. Error: {e}")
                    user_states[chat_id] = 'awaiting_amount'
            else:
                bot.sendMessage(chat_id, "Invalid input. Please enter a valid amount in INR using only numbers.")
                user_states[chat_id] = 'awaiting_amount'
        
        elif user_states[chat_id] and user_states[chat_id] != 'awaiting_amount':
            payment_id = user_states[chat_id]
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.get(
                f'https://api.razorpay.com/v1/payment_links/{payment_id}',
                auth=(razorpay_key, razorpay_secret),
                headers=headers
            )
            payment_data = response.json()
            payment_status = payment_data.get('status', 'unknown')
            if payment_status == 'paid':
                bot.sendMessage(chat_id, f"Payment of INR {amount / 100} received successfully! 😊")
                user_states[chat_id] = None  # Reset state
            else:
                bot.sendMessage(chat_id, f"Payment not yet received. Current status: {payment_status}. Please complete the payment.")

        elif command == '/cancel':
            bot.sendMessage(chat_id, "Payment process has been cancelled.")
            user_states[chat_id] = None
        else:
            bot.sendMessage(chat_id, "Command not recognized. Type /help for a list of commands.")

# Replace "YOUR_TELEGRAM_TOKEN" with your actual bot token
bot = telepot.Bot("7589607020:AAFnw92uMgmv695nT0SFDB9ZHwLWba3yG0k")
MessageLoop(bot, handle).run_as_thread()

# Keep the program running
while True:
    pass
