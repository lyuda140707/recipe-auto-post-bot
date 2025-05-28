import os
import logging
import asyncio
import aiohttp  # <-- ОБОВʼЯЗКОВО додай
from fastapi import FastAPI, Request
from aiogram import types
from bot_instance import dp, bot, check_and_post
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram import Bot
from fastapi import Response

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()


@app.on_event("startup")
async def startup():
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook встановлено")

    asyncio.create_task(check_and_post())     # Перевірка Google Таблиці
    asyncio.create_task(ping_self())          # Self-пінг для Render


@app.on_event("shutdown")
async def shutdown():
    logging.info("🛑 Webhook буде знято автоматично при зупинці")


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(update)
    return {"ok": True}


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return Response(content='{"status":"ok"}', media_type="application/json")


# Фонова задача для "підтримки життя"
async def ping_self():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://recipe-auto-bot.onrender.com/") as resp:
                    logging.info(f"🔃 Self-ping: {resp.status}")
        except Exception as e:
            logging.error(f"❌ Ping self error: {e}")
        await asyncio.sleep(240)  # Пінг кожні 4 хвилини
