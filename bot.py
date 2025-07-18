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

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Simple message handler
@router.message()
async def handle_message(message: types.Message):
    logging.info(f"📨 Received: {message.text}")
    await message.answer("✅ Received your message!")

# Startup
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set to {WEBHOOK_URL}")

# Shutdown
async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("🛑 Webhook deleted")

# Create aiohttp app and attach bot webhook
app = web.Application()
setup_application(app, dp, bot, on_startup=on_startup, on_shutdown=on_shutdown)
app.router.add_get("/", lambda request: web.Response(text="✅ Bot running"))

if __name__ == "__main__":
    web.run_app(app, port=8000)