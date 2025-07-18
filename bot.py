import os
import logging
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientPayloadError
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import Update

# 🚨 Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE")
BUNNY_API_KEY = os.getenv("BUNNY_API_KEY")
BUNNY_PULL_ZONE = os.getenv("BUNNY_PULL_ZONE")

# ✅ Check Required Variables
required_vars = [TELEGRAM_TOKEN, WEBHOOK_URL, BUNNY_STORAGE_ZONE, BUNNY_API_KEY, BUNNY_PULL_ZONE]
if not all(required_vars):
    raise RuntimeError("❌ Missing required environment variables.")

# 📝 Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🤖 Bot Setup
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# 📤 Upload to Bunny.net using streaming
async def upload_to_bunny(file_url, filename):
    bunny_url = f"https://storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}/{filename}"
    headers = {
        "AccessKey": BUNNY_API_KEY,
        "Content-Type": "application/octet-stream"
    }

    timeout = ClientTimeout(total=0)  # No timeout for large videos
    async with ClientSession(timeout=timeout) as session:
        async with session.get(file_url) as resp:
            if resp.status != 200:
                raise Exception(f"❌ Failed to download file. Status: {resp.status}")

            # Stream upload directly without reading into memory
            async with session.put(bunny_url, data=resp.content, headers=headers) as upload_resp:
                if upload_resp.status != 201:
                    error_text = await upload_resp.text()
                    raise Exception(f"❌ Bunny upload failed. Status: {upload_resp.status}, Detail: {error_text}")

    return f"https://{BUNNY_PULL_ZONE}/{filename}"

# 📥 Handle incoming message
@dp.message()
async def handle_link(message: types.Message):
    logger.info(f"📩 Received: {message.text}")
    parts = message.text.strip().split(" ", 1)

    if len(parts) != 2 or not parts[0].endswith(".mp4"):
        await message.reply("❌ Format:\n<code>filename.mp4 https://video-link</code>")
        return

    filename, file_url = parts[0], parts[1]

    try:
        await message.reply("⬇️ Downloading and uploading... Please wait.")
        cdn_url = await upload_to_bunny(file_url, filename)
        await message.reply(f"✅ Uploaded!\n<b>Watch:</b>\n<code>{cdn_url}</code>")
    except ClientPayloadError as e:
        logger.error(f"❌ Payload error: {e}")
        await message.reply("❌ Error: Incomplete download. Telegram file might be expired or link is broken.")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await message.reply(f"❌ Failed: {e}")

# 🌐 Webhook Setup
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

app = web.Application()
dp["bot"] = bot
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
app.on_startup.append(on_startup)
setup_application(app, dp, bot=bot)

# 🚀 Run Server
if __name__ == "__main__":
    logger.info("🚀 bot.py has started")
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))