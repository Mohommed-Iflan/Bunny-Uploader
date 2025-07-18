import os
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# Logging
logging.basicConfig(level=logging.INFO)
logging.info("🚀 bot.py has started")

# Environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not WEBHOOK_URL:
    raise Exception("❌ TELEGRAM_TOKEN or WEBHOOK_URL not set.")

# Bot setup
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Router
router = Router()
dp.include_router(router)

# Health check (for Railway 502 prevention)
async def health(request):
    return web.Response(text="✅ Bot is alive")

# Message handler
@router.message()
async def handle_all(message: types.Message):
    logging.info(f"📨 Message from {message.from_user.id}: {message.text}")
    await message.answer("✅ Message received!")

# Webhook startup
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set: {WEBHOOK_URL}")

# Webhook shutdown
async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("🛑 Bot shutdown")

# aiohttp app
app = web.Application()
app.router.add_get("/", health)
app.router.add_post("/", dp.webhook_handler(bot))
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=8000)