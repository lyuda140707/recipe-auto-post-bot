import os
import logging
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
    # фоновий процес розсилки
    dp.loop.create_task(check_and_post())

@app.on_event("shutdown")
async def shutdown():
    await bot.delete_webhook()
    logging.info("🛑 Webhook знято")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(update)
    return {"ok": True}
