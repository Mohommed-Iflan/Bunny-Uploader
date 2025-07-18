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
BUNNY_STORAGE_HOST = os.getenv("BUNNY_STORAGE_HOST")  # e.g., storage.bunnycdn.com
BUNNY_PULL_ZONE = os.getenv("BUNNY_PULL_ZONE")        # e.g., myzone.b-cdn.net

# Verify required variables
required_vars = [
    TELEGRAM_TOKEN, WEBHOOK_URL,
    BUNNY_STORAGE_ZONE, BUNNY_API_KEY,
    BUNNY_STORAGE_HOST, BUNNY_PULL_ZONE
]
if not all(required_vars):
    raise RuntimeError("❌ Missing required environment variables.")

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message()
async def handle_link(message: types.Message):
    text = message.text.strip()
    logging.info(f"📩 Received: {text}")

    # Expect format: filename.mp4 https://t.me/...
    parts = text.split()
    if len(parts) != 2:
        await message.answer("❌ Format:\n&lt;filename&gt;.mp4 &lt;telegram_file_link&gt;")
        return

    filename, file_link = parts
    if not filename.endswith(".mp4"):
        await message.reply("❌ Filename must end with .mp4")
        return

    await message.reply("⏳ Downloading from Telegram and uploading to BunnyCDN...")

    try:
        # Download the video from Telegram link
        async with aiohttp.ClientSession() as session:
            async with session.get(file_link) as resp:
                if resp.status != 200:
                    await message.reply(f"❌ Failed to download file: status {resp.status}")
                    return
                data = await resp.read()

        # Upload to BunnyCDN
        upload_url = f"https://{BUNNY_STORAGE_HOST}/{BUNNY_STORAGE_ZONE}/{filename}"
        headers = {
            "AccessKey": BUNNY_API_KEY,
            "Content-Type": "application/octet-stream",
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(upload_url, data=data, headers=headers) as resp:
                if resp.status == 201:
                    cdn_url = f"https://{BUNNY_PULL_ZONE}/{filename}"
                    await message.reply(f"✅ Uploaded successfully:\n🎬 {cdn_url}")
                else:
                    await message.reply(f"❌ Upload failed with status {resp.status}")

    except Exception as e:
        logging.error(f"❌ Error: {e}")
        await message.reply(f"❌ Upload failed: {e}")

# Webhook startup and shutdown
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set to {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("🛑 Webhook deleted")

# Create aiohttp app
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=int(os.getenv("PORT", 8000)))