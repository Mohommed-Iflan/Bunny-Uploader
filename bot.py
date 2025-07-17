import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Enable logging
logging.basicConfig(level=logging.INFO)

# Load Telegram Bot Token from Railway environment variable
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Create bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Handle all incoming messages
@dp.message()
async def echo_handler(message: types.Message):
    logging.info(f"Received message: {message.text}")
    await message.answer("✅ Got your message!")

# Health check route (for browser or Railway status page)
async def health(request):
    return web.Response(text="✅ Bot is running!")

# Set webhook when server starts
async def on_startup(app):
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/"
    await bot.set_webhook(webhook_url)
    logging.info(f"🚀 Webhook set to: {webhook_url}")

# Create web app and configure webhook routes
app = web.Application()
app.router.add_get("/", health)  # Optional route for / test
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot)
app.on_startup.append(on_startup)

# Run the bot web server
if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))