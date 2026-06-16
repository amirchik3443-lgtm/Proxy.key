import os
import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Твой токен от @BotFather
TELEGRAM_TOKEN = "8736266436:AAG_mcrUeFtHTd3wgCkxcU-ImKSInAlDB9k"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Наша база данных ключей и привязанных к ним прокси
KEYS_DATABASE = {
    "VALID-KEY-1234": {
        "is_active": True,
        "proxy_config": "192.168.1.50:8080:user:pass"
    },
    "FREEFIRE-VIP-777": {
        "is_active": True,
        "proxy_config": "185.233.10.5:8000:user342:pass99"
    }
}

# --- МАРШРУТЫ ДЛЯ САЙТА (FASTAPI) ---

@app.get("/")
def read_root():
    return {"status": "Бот и сайт успешно запущены!"}

@app.get("/check_key/{key}")
def check_key(key: str):
    if key in KEYS_DATABASE:
        key_data = KEYS_DATABASE[key]
        if key_data["is_active"]:
            return {"status": "success", "proxy": key_data["proxy_config"]}
        else:
            raise HTTPException(status_code=400, detail="Ключ деактивирован")
    raise HTTPException(status_code=404, detail="Ключ не найден")

# --- ЛОГИКА ТЕЛЕГРАМ БОТА ---

@app.post(f"/webhook/{TELEGRAM_TOKEN}")
async def telegram_webhook(update: dict):
    """Этот адрес будет вызывать сам Telegram, когда боту пишут сообщения"""
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        # Команда /start
        if text == "/start":
            reply_text = (
                "👋 Привет! Я твой личный прокси-бот.\n\n"
                "Отправь мне лицензионный ключ, чтобы проверить его "
                "и получить настройки прокси-сервера!"
            )
            send_message(chat_id, reply_text)
        
        # Если пользователь отправил любой другой текст (проверяем как ключ)
        else:
            send_message(chat_id, "⌛ Проверяю ключ...")
            
            if text in KEYS_DATABASE:
                key_data = KEYS_DATABASE[text]
                if key_data["is_active"]:
                    success_text = (
                        "✅ Ключ успешно активирован!\n\n"
                        f"🔑 Ваш ключ: `{text}`\n"
                        f"🌐 Данные прокси: `{key_data['proxy_config']}`"
                    )
                    send_message(chat_id, success_text)
                else:
                    send_message(chat_id, "❌ Этот ключ деактивирован владельцем.")
            else:
                send_message(chat_id, "❌ Ошибка: Ключ не найден в базе данных. Попробуйте другой.")

    return {"status": "ok"}

def send_message(chat_id: int, text: str):
    """Функция отправки сообщения пользователю в Telegram"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"  # Чтобы красиво подсвечивать ключи и прокси
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")
