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
dp = Dispatcher(bot)
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
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="📱 Відкрити меню",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )
    await message.answer("Привіт! 👋 Щоб переглядати рецепти — натисни кнопку нижче ⬇️", reply_markup=keyboard)



# Background task
# Background task
async def check_and_post():
    while True:
        try:
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            data = sheet.get_all_records()

            for idx, row in enumerate(data, start=2):
                try:
                    status = (row.get("Статус") or "").strip().lower()
                    if status != "очікує":
                        continue

                    scheduled_time = (row.get("Дата і час") or "").strip()
                    if scheduled_time != now:
                        continue

                    text = (row.get("Текст рецепта") or "").strip()
                    description = (row.get("Опис рецепта") or "").strip()
                    photo = (row.get("Фото") or "").strip()
                    recipe_id = str(row.get("ID рецепта") or "").strip()

                    caption = f"""🍽 <b>{text}</b>

{description}

👀 Натисни кнопку нижче, щоб переглянути рецепт у боті Рецептик.
🔎 Знайди за назвою: <b>{text}</b>"""

                    keyboard = InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="👨‍🍳 Відкрити Рецептик 🍲",
                            url="https://t.me/recept_kitchen_bot"
                        )
                    )

                    if photo:
                        await bot.send_photo(CHANNEL_USERNAME, photo=photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
                    else:
                        await bot.send_message(CHANNEL_USERNAME, text=caption, reply_markup=keyboard, parse_mode="HTML")

                    sheet.update_cell(idx, 6, "Опубліковано")  # колонка Статус = 6
                    logging.info(f"📤 Рецепт ID {recipe_id} надіслано")
                except Exception as inner_err:
                    logging.error(f"⚠️ Помилка в рядку {idx}: {inner_err}")

        except Exception as e:
            logging.error(f"❌ Глобальна помилка в check_and_post: {e}")

        await asyncio.sleep(60)
