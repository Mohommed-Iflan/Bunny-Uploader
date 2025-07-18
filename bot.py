import os
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

logging.basicConfig(level=logging.INFO)
logging.info("🚀 bot.py has started")

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE")
BUNNY_API_KEY = os.getenv("BUNNY_API_KEY")
BUNNY_STORAGE_HOST = os.getenv("BUNNY_STORAGE_HOST")  # Example: storage.bunnycdn.com

# Validate env
if not all([TELEGRAM_TOKEN, WEBHOOK_URL, BUNNY_STORAGE_ZONE, BUNNY_API_KEY, BUNNY_STORAGE_HOST]):
    raise Exception("❌ Missing environment variables.")

# Setup bot
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Message handler
@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()

    if not text.startswith("http"):
        await message.reply("❌ Please send a direct download link.")
        return

    logging.info(f"📩 Received: {text}")
    await message.reply("⬇️ Downloading video...")

    try:
        # Extract filename from link (e.g., /stream/90?hash=xxx → 90.mp4)
        base_name = text.split("/")[-1].split("?")[0]
        if not base_name.lower().endswith(".mp4"):
            base_name += ".mp4"

        # Download the video content
        async with aiohttp.ClientSession() as session:
            async with session.get(text) as resp:
                if resp.status != 200:
                    raise Exception(f"Download failed with status {resp.status}")
                video_data = await resp.read()

        # Upload to Bunny
        upload_url = f"https://{BUNNY_STORAGE_HOST}/{BUNNY_STORAGE_ZONE}/{base_name}"
        headers = {"AccessKey": BUNNY_API_KEY, "Content-Type": "application/octet-stream"}

        async with aiohttp.ClientSession() as session:
            async with session.put(upload_url, headers=headers, data=video_data) as resp:
                if resp.status != 201:
                    raise Exception(f"Bunny upload failed: {resp.status}")
        
        stream_url = f"https://video.bunnycdn.com/{base_name}"
        await message.reply(f"✅ Uploaded successfully!\n🎥 {stream_url}")

    except Exception as e:
        logging.error(f"❌ Error: {e}")
        await message.reply(f"❌ Upload failed: {e}")

# Startup and shutdown
async def on_startup(bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set: {WEBHOOK_URL}")

async def on_shutdown(bot):
    await bot.delete_webhook()
    logging.info("🛑 Bot shutdown")

# Web app (for Railway/Koyeb)
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=8000)