import os
import json
import logging
from datetime import datetime
import pytz
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Logging
logging.basicConfig(level=logging.INFO)

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
WEBAPP_URL = os.getenv("WEBAPP_URL")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Kyiv")

# Bot init
bot = Bot(token=BOT_TOKEN)
import asyncio
loop = asyncio.get_event_loop()
dp = Dispatcher(bot, loop=loop)
tz = pytz.timezone(TIMEZONE)

# Google Sheets auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/12wRAEC2B0BN135jaNLCMhgFXaIJowKLwq0S9wSJkoxQ/edit").sheet1

# Handler for /start
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

# Background task
async def check_and_post():
    while True:
        try:
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            data = sheet.get_all_records()

            for idx, row in enumerate(data, start=2):
                status = row.get("Статус", "").strip().lower()
                if status != "чекає":
                    continue

                scheduled_time = row.get("Дата і час", "").strip()
                if scheduled_time != now:
                    continue

                text = row.get("Текст рецепта", "").strip()
                photo = row.get("Фото (URL)", "").strip()
                recipe_id = str(row.get("ID рецепта", "")).strip()

                caption = f"{text}\n\n👀 Натисни, щоб побачити повний рецепт"
                keyboard = InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="👀 Подивитись повністю",
                        url=f"https://t.me/{(await bot.get_me()).username}?start=recipe{recipe_id}"
                    )
                )

                if photo:
                    await bot.send_photo(CHANNEL_USERNAME, photo=photo, caption=caption, reply_markup=keyboard)
                else:
                    await bot.send_message(CHANNEL_USERNAME, text=caption, reply_markup=keyboard)

                sheet.update_cell(idx, 5, "Опубліковано")
                logging.info(f"📤 Рецепт ID {recipe_id} надіслано")
        except Exception as e:
            logging.error(f"❌ Помилка під час розсилки: {e}")

        await asyncio.sleep(60)
