import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Logging
logging.basicConfig(level=logging.INFO)
logging.info("🚀 bot.py has started")

# Load from env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not WEBHOOK_URL:
    raise Exception("❌ TELEGRAM_TOKEN or WEBHOOK_URL not set.")

# Bot and Dispatcher
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Message handler
@router.message()
async def handle_message(message: types.Message):
    logging.info(f"📩 Received: {message.text}")
    await message.answer("✅ Message received!")

# Startup and Shutdown
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set to: {WEBHOOK_URL}")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logging.info("🛑 Webhook deleted")

# AIOHTTP app
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Handle Telegram updates
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")

# Optional home page
app.router.add_get("/", lambda request: web.Response(text="✅ Bot is running"))

if __name__ == "__main__":
    web.run_app(app, port=8000)