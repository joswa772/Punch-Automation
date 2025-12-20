import os
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
msg = "✅ Test message from Punch Script"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = {"chat_id": chat_id, "text": msg}
response = requests.post(url, data=data)

print(response.status_code)
print(response.text)
