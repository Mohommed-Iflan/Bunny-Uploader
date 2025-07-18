import os
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Setup logging
logging.basicConfig(level=logging.INFO)

# Bot token and Bunny config from environment
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
BUNNY_STORAGE_KEY = os.getenv("BUNNY_STORAGE_KEY")
BUNNY_STORAGE_NAME = os.getenv("BUNNY_STORAGE_NAME")  # e.g. benthamizha
BUNNY_HOST = os.getenv("BUNNY_HOST")  # e.g. storage.bunnycdn.com
BUNNY_PULLZONE_URL = os.getenv("BUNNY_PULLZONE_URL")  # e.g. https://stream.benthamizha.online/

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Handle videos
@dp.message()
async def handle_video(message: types.Message):
    if not message.video:
        await message.reply("❌ Please send a video file.")
        return

    file_id = message.video.file_id
    file = await bot.get_file(file_id)

    telegram_file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    file_name = file.file_path.split("/")[-1]

    logging.info(f"📥 Received video: {file_name}")
    logging.info(f"➡️ Telegram file URL: {telegram_file_url}")

    # Upload to Bunny
    bunny_url = f"https://{BUNNY_HOST}/{BUNNY_STORAGE_NAME}/{file_name}"
    headers = {
        "AccessKey": BUNNY_STORAGE_KEY,
        "Content-Type": "application/octet-stream"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(telegram_file_url) as tg_resp:
            if tg_resp.status != 200:
                await message.reply("❌ Failed to download video from Telegram.")
                return
            video_data = await tg_resp.read()

        async with session.put(bunny_url, data=video_data, headers=headers) as bunny_resp:
            if bunny_resp.status != 201:
                await message.reply(f"❌ Bunny upload failed ({bunny_resp.status}).")
                return

    # Construct and reply with BunnyCDN URL
    video_link = f"{BUNNY_PULLZONE_URL.rstrip('/')}/{file_name}"
    await message.reply(f"✅ Uploaded!\n🎬 Watch: {video_link}")

# Health check
async def health(request):
    return web.Response(text="Bot is running")

async def on_startup(app):
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/"
    await bot.set_webhook(webhook_url)
    logging.info(f"🚀 Webhook set to: {webhook_url}")

app = web.Application()
app.router.add_get("/", health)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))