import requests

BOT_TOKEN = "8598412780:AAFTMoUyEvB06cusjUs7qcvSjhNX4OlVF5Y"
CHAT_ID = "@notitranningvcc"  # hoặc -100xxxxxxxxxx

message = "Xin chào từ Đoàn Phúc 🚀"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

payload = {
    "chat_id": CHAT_ID,
    "text": message
}

response = requests.post(url, data=payload)

print(response.json())