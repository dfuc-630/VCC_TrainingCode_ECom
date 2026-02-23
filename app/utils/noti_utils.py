import requests

BOT_TOKEN = "8598412780:AAFTMoUyEvB06cusjUs7qcvSjhNX4OlVF5Y"
CHAT_ID = "@notitranningvcc"  # hoặc -100xxxxxxxxxx

def send_tele_message(message = None, order_id = None, status = True):
    if not message:
        if status is True and order_id is not None:
            message = f"Order {order_id} is completed"
        elif status is False and order_id is not None:
            message = f"Order {order_id} is failed"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=payload)

    print(response.json())