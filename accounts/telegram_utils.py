import asyncio
from telegram import Bot

BOT_TOKEN = '7602255958:AAFAQiMsWphke4GwGb9vWXBxiolJgNi6L-g'

async def send_telegram_message_async(chat_id, message):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

def send_telegram_message(chat_id, message):
    try:
        asyncio.run(send_telegram_message_async(chat_id, message))
    except Exception as e:
        print("Telegram Error:", e)
