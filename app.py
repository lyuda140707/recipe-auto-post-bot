import os
import logging
import asyncio  # 🔺 ОЦЕ додати
from fastapi import FastAPI, Request
from aiogram import types
from bot_instance import dp, bot, check_and_post
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram import Bot

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

@app.on_event("startup")
async def startup():
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook встановлено")

    # Старт фонової задачі
    asyncio.create_task(check_and_post())

    # Утримує FastAPI сервіс живим
    asyncio.create_task(wait_forever())

# Додаємо функцію, яка "вічно чекає"
async def wait_forever():
    while True:
        await asyncio.sleep(3600)


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

@app.get("/")
async def root():
    return {"status": "ok"}
