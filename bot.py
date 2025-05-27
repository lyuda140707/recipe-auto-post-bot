import os
import json
import logging
import asyncio
from datetime import datetime
import pytz
from io import StringIO

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.executor import start_polling

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Logging
logging.basicConfig(level=logging.INFO)

# Load from .env or Render env vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # e.g. @receptukTop
TIMEZONE = os.getenv("TIMEZONE", "Europe/Kyiv")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://lyuda140707.github.io/telegram-recipe-webapp/")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Timezone-aware datetime
tz = pytz.timezone(TIMEZONE)

# Google Sheets setup via JSON in env
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
creds_dict = json.loads(google_creds_raw)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/12wZ-u-lr1uBawVKQn8Oq5qkRg5JJDwAzsYCgUexwUw8/edit").sheet1




# === Handle /start with recipe ===
@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    args = message.get_args()
    if args.startswith("recipe"):
        recipe_id = args.replace("recipe", "")
        webapp_link = f"{WEBAPP_URL}?id={recipe_id}"
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("👀 Відкрити рецепт", web_app=WebAppInfo(url=webapp_link))
        )
        await message.answer("Ось повний рецепт 👇", reply_markup=keyboard)
    else:
        await message.answer("Привіт! Тут ти зможеш знайти рецепти 🍽")


# === Background task to check sheet ===
async def check_and_post():
    while True:
        try:
            data = sheet.get_all_records()
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

            for idx, row in enumerate(data, start=2):  # start=2 to match row index in Google Sheet
                text = row.get("Текст рецепта")
                scheduled_time = row.get("Дата і час")
                photo_url = row.get("Фото (URL)")
                recipe_id = row.get("ID рецепта")
                status = row.get("Статус").strip().lower()

                if status == "чекає" and scheduled_time == now:
                    caption = f"{text}\n\n👀 Натисни, щоб побачити повний рецепт"
                    keyboard = InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="👀 Подивитись повністю",
                            url=f"https://t.me/{(await bot.get_me()).username}?start=recipe{recipe_id}"
                        )
                    )
                    if photo_url:
                        await bot.send_photo(CHANNEL_USERNAME, photo=photo_url, caption=caption, reply_markup=keyboard)
                    else:
                        await bot.send_message(CHANNEL_USERNAME, text=caption, reply_markup=keyboard)

                    # Mark as sent
                    sheet.update_cell(idx, 5, "Опубліковано")
                    logging.info(f"📤 Надіслано рецепт ID {recipe_id} у канал")
        except Exception as e:
            logging.error(f"Помилка: {e}")

        await asyncio.sleep(60)  # перевіряти щохвилини


# === Main ===
async def on_startup(_):
    asyncio.create_task(check_and_post())

if __name__ == "__main__":
    start_polling(dp, on_startup=on_startup)
