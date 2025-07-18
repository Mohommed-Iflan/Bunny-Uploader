import os
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Enable logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE")
BUNNY_API_KEY = os.getenv("BUNNY_API_KEY")
BUNNY_STORAGE_HOST = os.getenv("BUNNY_STORAGE_HOST")  # Example: storage.bunnycdn.com

# Verify all variables
required_vars = [TELEGRAM_TOKEN, WEBHOOK_URL, BUNNY_STORAGE_ZONE, BUNNY_API_KEY, BUNNY_STORAGE_HOST]
if not all(required_vars):
    raise RuntimeError("❌ Missing required environment variables.")

# Initialize Bot and Dispatcher
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Handle all messages
@dp.message()
async def handle_video_link(message: types.Message):
    url = message.text.strip()

    if not url.startswith("http"):
        await message.answer("❌ Please send a direct video URL.")
        return

    logging.info(f"📩 Received: {url}")
    await message.answer("⬇️ Downloading video...")

    try:
        # Extract filename from link
        base_name = url.split("/")[-1].split("?")[0]
        if not base_name.endswith(".mp4"):
            base_name += ".mp4"

        # Download the video
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Download failed with status {resp.status}")
                video_data = await resp.read()

        # Upload to Bunny
        upload_url = f"https://{BUNNY_STORAGE_HOST}/{BUNNY_STORAGE_ZONE}/{base_name}"
        headers = {
            "AccessKey": BUNNY_API_KEY,
            "Content-Type": "application/octet-stream"
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(upload_url, headers=headers, data=video_data) as upload_resp:
                if upload_resp.status != 201:
                    raise Exception(f"Bunny upload failed with status {upload_resp.status}")

        stream_url = f"https://video.bunnycdn.com/{base_name}"
        await message.answer(f"✅ Uploaded successfully!\n🎥 {stream_url}")

    except Exception as e:
        logging.error(f"❌ Error: {e}")
        await message.answer(f"❌ Upload failed: {e}")

# Webhook setup
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set to {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("🛑 Webhook deleted")

# Setup aiohttp app
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=int(os.getenv("PORT", 8000)))