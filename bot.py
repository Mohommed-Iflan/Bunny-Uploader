import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# ✅ Logging enabled
logging.basicConfig(level=logging.INFO)
logging.info("🚀 bot.py has started")

# ✅ Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not WEBHOOK_URL:
    raise Exception("❌ TELEGRAM_TOKEN or WEBHOOK_URL not set.")

# ✅ Telegram bot setup
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# ✅ Health check route (prevents 502 error)
async def health(request):
    return web.Response(text="✅ Bot is alive")

# ✅ Webhook message handler
@dp.message()
async def handle_all(message: types.Message):
    logging.info(f"📩 Received message: {message.text}")
    await message.answer("✅ Message received!")

# ✅ Webhook startup
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set to: {WEBHOOK_URL}")

# ✅ Shutdown handler
async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("🛑 Bot shutdown")

# ✅ Web server setup
app = web.Application()
app.router.add_get("/", health)  # for health check
app.router.add_post("/", dp.as_handler())  # Telegram webhook handler
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# ✅ Run app
if __name__ == "__main__":
    web.run_app(app, port=8000)