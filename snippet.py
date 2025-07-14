import requests

bot_token = "7733717490:AAFxmJywOnkk0Jmwqymc2OMNFhOBtraVdEc"
chat_id = 1664758926
text = "Hello from direct test!"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
resp = requests.post(url, data={"chat_id": chat_id, "text": text})

print(resp.status_code, resp.json())
