import os
import logging
import requests
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import FSInputFile

# Load secrets from Railway Environment Variables
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
BUNNY_STORAGE_NAME = os.getenv("BUNNY_STORAGE_NAME")
BUNNY_STORAGE_HOST = os.getenv("BUNNY_STORAGE_HOST")
BUNNY_ACCESS_KEY = os.getenv("BUNNY_ACCESS_KEY")

if not BOT_TOKEN:
    raise Exception("❌ TELEGRAM_TOKEN environment variable not set.")
if not BUNNY_STORAGE_NAME or not BUNNY_STORAGE_HOST or not BUNNY_ACCESS_KEY:
    raise Exception("❌ Bunny.net environment variables not set.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Health check route
async def health(request):
    return web.Response(text="✅ Bot is running!")

# Handle video messages
@dp.message(F.video)
async def handle_video(message: types.Message):
    logging.info("📥 Video received")

    # Download video from Telegram
    file_info = await bot.get_file(message.video.file_id)
    file_path = file_info.file_path
    file_name = f"{message.video.file_unique_id}.mp4"
    telegram_file = await bot.download_file(file_path)

    # Save to temp file
    with open(file_name, "wb") as f:
        f.write(telegram_file.read())

    # Upload to Bunny.net
    upload_url = f"https://{BUNNY_STORAGE_HOST}/{BUNNY_STORAGE_NAME}/{file_name}"
    with open(file_name, "rb") as f:
        headers = {
            "AccessKey": BUNNY_ACCESS_KEY,
            "Content-Type": "application/octet-stream"
        }
        response = requests.put(upload_url, data=f, headers=headers)

    if response.status_code == 201:
        await message.answer(f"✅ Video uploaded to Bunny.net!\n\n📤 `{file_name}`")
    else:
        await message.answer(f"❌ Upload failed: {response.status_code}")

    os.remove(file_name)

# Fallback text reply
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer("📥 Send me a video and I’ll upload it to Bunny.net!")

# Setup app and webhook
app = web.Application()
app.router.add_get("/", health)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot)

async def on_startup(app):
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/"
    await bot.set_webhook(webhook_url)
    logging.info(f"🚀 Webhook set: {webhook_url}")

app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))