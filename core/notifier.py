import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_telegram(message: str) -> None:
    """
    Send message to TELEGRAM_CHAT_ID via TELEGRAM_BOT_TOKEN using requests.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Telegram message sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")