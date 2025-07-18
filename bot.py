import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

# Load .env file if running locally
load_dotenv()

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BUNNY_API_KEY = os.getenv("BUNNY_API_KEY")
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE")
BUNNY_STORAGE_REGION = os.getenv("BUNNY_STORAGE_REGION", "storage.bunnycdn.com")
BUNNY_PULLZONE_HOSTNAME = os.getenv("BUNNY_PULLZONE_HOSTNAME")  # e.g. stream.benthamizha.online

if not TELEGRAM_TOKEN:
    raise Exception("❌ TELEGRAM_TOKEN environment variable not set.")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Start command
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("✅ Send me a video (up to 2GB) and I’ll upload it to BunnyCDN!")

# Video handler
@dp.message(F.video)
async def handle_video(message: Message):
    video = message.video
    file_id = video.file_id

    try:
        # Get Telegram file path
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        # Generate direct download URL
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        logging.info(f"📥 Telegram File URL: {file_url}")

        # Use file name or fallback
        filename = video.file_name or f"{file_id}.mp4"

        # Upload to Bunny
        uploaded_url = await upload_to_bunny(file_url, filename)

        if uploaded_url:
            await message.reply(f"✅ Video uploaded!\n\n🎬 [Watch Here]({uploaded_url})", parse_mode="Markdown")
        else:
            await message.reply("❌ Upload failed. Please try again.")

    except Exception as e:
        logging.error(f"Error handling video: {e}")
        await message.reply("⚠️ An error occurred while processing your video.")

# Upload function
async def upload_to_bunny(file_url, filename):
    url = f"https://{BUNNY_STORAGE_REGION}/{BUNNY_STORAGE_ZONE}/{filename}"

    headers = {
        "AccessKey": BUNNY_API_KEY,
        "Content-Type": "application/octet-stream"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as file_response:
                if file_response.status != 200:
                    logging.error(f"Failed to download from Telegram: {file_response.status}")
                    return None
                file_data = await file_response.read()

            async with session.put(url, data=file_data, headers=headers) as upload_response:
                if upload_response.status == 201:
                    logging.info("✅ Uploaded to Bunny successfully")
                    return f"https://{BUNNY_PULLZONE_HOSTNAME}/{filename}"
                else:
                    logging.error(f"Upload to Bunny failed: {upload_response.status}")
                    return None

    except Exception as e:
        logging.error(f"Exception during Bunny upload: {e}")
        return None

# Webhook setup
async def on_startup(app):
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        await bot.set_webhook(webhook_url)
        logging.info(f"🚀 Webhook set to: {webhook_url}")
    else:
        logging.warning("⚠️ No WEBHOOK_URL set.")

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
app.on_startup.append(on_startup)
setup_application(app, dp, bot=bot)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8000)