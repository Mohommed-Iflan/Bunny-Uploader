import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Enable logging
logging.basicConfig(level=logging.INFO)

# Load Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise Exception("❌ TELEGRAM_TOKEN environment variable not set.")

# Load Railway static URL for webhook
RAILWAY_URL = os.getenv("RAILWAY_STATIC_URL")
if not RAILWAY_URL:
    raise Exception("❌ RAILWAY_STATIC_URL environment variable not set.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    logging.info(f"📩 Received: {message.text}")
    await message.answer("✅ Received your message!")

async def health_check(request):
    return web.Response(text="✅ Bot is running.")

async def on_startup(app):
    webhook_url = f"https://{RAILWAY_URL}/"
    await bot.set_webhook(webhook_url)
    logging.info(f"🚀 Webhook set to: {webhook_url}")

app = web.Application()
app.router.add_get("/", health_check)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))