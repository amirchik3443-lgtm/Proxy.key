from fastapi import FastAPI, Request
import requests

app = FastAPI()

TOKEN = "8736266436:AAG_mcrUeFtHTd3wgCkxcU-ImKSInAlDB9k"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# База данных ключей (вместо прокси теперь храним привязанный IP)
# Если IP равен None, значит ключ еще не привязан
KEYS_DB = {
    "FREEFIRE-VIP-777": None,
    "H8TZ-4MQN-7XKP-1VRC": None
}

# Временное хранилище, чтобы бот помнил, какой шаг выполняет пользователь
# Структура: { chat_id: {"key": "НАЗВАНИЕ_КЛЮЧА", "stage": "waiting_for_ip", "pending_ip": "IP"} }
USER_STATES = {}

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != TOKEN:
        return {"status": "unauthorized"}

    data = await request.json()

    # 1. ОБРАБОТКА НАЖАТИЯ НА КНОПКИ (Callback Query)
    if "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        callback_data = callback["data"]

        state = USER_STATES.get(chat_id)
        if not state or state.get("stage") != "waiting_for_confirm":
            send_message(chat_id, "❌ Сессия истекла или недействительна. Отправьте ключ заново.")
            return {"status": "ok"}

        key = state["key"]
        pending_ip = state["pending_ip"]

        if callback_data == "confirm_ip":
            # Сохраняем IP в нашу "базу данных"
            KEYS_DB[key] = pending_ip
            
            success_text = (
                f"✅ **IP Updated Successfully!**\n\n"
                f"🔑 **Key:** `{key}`\n"
                f"🌐 **New IP:** {pending_ip}"
            )
            send_message(chat_id, success_text)
            # Очищаем состояние пользователя
            USER_STATES.pop(chat_id, None)

        elif callback_data == "cancel_ip":
            send_message(chat_id, "❌ Изменение IP-адреса отменено.")
            USER_STATES.pop(chat_id, None)

        return {"status": "ok"}

    # 2. ОБРАБОТКА ОБЫЧНЫХ ТЕКСТОВЫХ СООБЩЕНИЙ
    if "message" in data and "text" in data["message"]:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message["text"].strip()

        # Команда /start
        if text == "/start":
            USER_STATES.pop(chat_id, None) # сброс при перезапуске
            send_message(chat_id, "👋 Привет! Я твой личный прокси-бот.\n\nОтправь мне лицензионный ключ, чтобы проверить его и получить настройки прокси-сервера!")
            return {"status": "ok"}

        # Проверяем, на каком шаге пользователь
        state = USER_STATES.get(chat_id)

        # ШАГ 2: Пользователь уже ввел ключ и сейчас прислал IP-адрес
        if state and state.get("stage") == "waiting_for_ip":
            # Простейшая проверка, что это похоже на IP (содержит точки)
            if "." in text and len(text) >= 7:
                state["pending_ip"] = text
                state["stage"] = "waiting_for_confirm"

                # Создаем инлайн-кнопки Confirm и Cancel как на скриншоте
                inline_keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "  Confirm", "callback_data": "confirm_ip"},
                            {"text": "❌ Cancel", "callback_data": "cancel_ip"}
                        ]
                    ]
                }

                confirm_message = f"Confirm IP change for key\n{state['key']} to {text}?"
                send_message(chat_id, confirm_message, reply_markup=inline_keyboard)
            else:
                send_message(chat_id, "❌ Это не похоже на правильный IP-адрес. Пожалуйста, отправьте корректный IP (например, 95.87.67.4).")
            return {"status": "ok"}

        # ШАГ 1: Пользователь просто отправил текст (проверяем, ключ ли это)
        if text in KEYS_DB:
            # Запоминаем, что этот чат сейчас привязывает конкретный ключ
            USER_STATES[chat_id] = {
                "key": text,
                "stage": "waiting_for_ip",
                "pending_ip": None
            }
            
            reply_text = f"  Key verified: {text}\nPlease send your new IP address."
            send_message(chat_id, reply_text)
        else:
            # Если это не ключ и бот не ждал IP
            send_message(chat_id, "❌ Неверный ключ. Пожалуйста, проверьте правильность ввода или обратитесь к администратору.")

    return {"status": "ok"}
