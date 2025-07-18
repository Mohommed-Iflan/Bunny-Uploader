import os
import aiohttp
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

logging.basicConfig(level=logging.INFO)
logging.info("🚀 bot.py has started")

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BUNNY_API_KEY = os.getenv("BUNNY_API_KEY")
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE")
BUNNY_STORAGE_HOST = os.getenv("BUNNY_STORAGE_HOST")  # e.g., storage.bunnycdn.com

# Basic check
if not all([TELEGRAM_TOKEN, WEBHOOK_URL, BUNNY_API_KEY, BUNNY_STORAGE_ZONE, BUNNY_STORAGE_HOST]):
    raise Exception("❌ Missing environment variables.")

bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Function to download and upload video
async def upload_to_bunny(video_url: str, filename: str) -> str:
    try:
        # Step 1: Download the video
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as resp:
                if resp.status != 200:
                    raise Exception(f"Download failed: {resp.status}")
                video_data = await resp.read()

        # Step 2: Upload to Bunny
        upload_url = f"https://{BUNNY_STORAGE_HOST}/{BUNNY_STORAGE_ZONE}/{filename}"
        headers = {
            "AccessKey": BUNNY_API_KEY,
            "Content-Type": "application/octet-stream"
        }
        async with aiohttp.ClientSession() as session:
            async with session.put(upload_url, data=video_data, headers=headers) as resp:
                if resp.status not in [201, 200]:
                    raise Exception(f"Bunny upload failed: {resp.status}")
        
        # Return streaming link
        return f"https://{BUNNY_STORAGE_HOST.replace('storage.', 'video.')}/{filename}"

    except Exception as e:
        logging.error(f"⚠️ Error during upload: {e}")
        return f"❌ Upload failed: {str(e)}"

# Main message handler
@dp.message()
async def handle_all(message: types.Message):
    text = message.text.strip()

    if not text.startswith("http"):
        await message.answer("⚠️ Please send a valid direct video link.")
        return

    logging.info(f"📩 Received: {text}")
    filename = text.split("/")[-1].split("?")[0]  # Extract filename from URL

    await message.answer("⏳ Uploading your video to BunnyCDN...")

    result = await upload_to_bunny(text, filename)

    await message.answer(result)

# Webhook startup
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set: {WEBHOOK_URL}")

# Webhook shutdown
async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("🛑 Bot shutdown")

# Web server config
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Setup webhook route
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp)

if __name__ == "__main__":
    web.run_app(app, port=8000)