import requests
import logging

logger = logging.getLogger(__name__)

BOT_TOKEN = "8598412780:AAFTMoUyEvB06cusjUs7qcvSjhNX4OlVF5Y"
CHAT_ID = "@notitranningvcc"

def send_tele_message(order_id: str = None, status: bool = True, message: str = None):
    """Gửi tin nhắn tới Telegram"""
    if not message:
        status_text = "completed" if status else "failed"
        message = f"Order {order_id} is {status_text}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Telegram API Error: {e}")
        return None