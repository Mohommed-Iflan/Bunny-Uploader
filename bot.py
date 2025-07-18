import os
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Load environment variables
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
BUNNY_API_KEY = os.getenv("BUNNY_API_KEY")  # Bunny Storage Zone API Key
BUNNY_STORAGE_NAME = os.getenv("BUNNY_STORAGE_NAME")  # Storage zone name
BUNNY_UPLOAD_DIR = os.getenv("BUNNY_UPLOAD_DIR", "")  # Optional sub-folder

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(lambda message: message.video or message.document)
async def handle_video(message: types.Message):
    file = message.video or message.document
    file_id = file.file_id
    file_name = file.file_name or f"{file_id}.mp4"

    # Get file path
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    logging.info(f"📥 Video received: {file_name}")
    logging.info(f"🔗 Telegram file URL: {download_url}")

    # Prepare Bunny.net upload URL
    upload_url = f"https://storage.bunnycdn.com/{BUNNY_STORAGE_NAME}"
    if BUNNY_UPLOAD_DIR:
        upload_url += f"/{BUNNY_UPLOAD_DIR}"
    upload_url += f"/{file_name}"

    # Upload to Bunny.net
    headers = {
        "AccessKey": BUNNY_API_KEY,
        "Content-Type": "application/octet-stream"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as tg_response:
            if tg_response.status == 200:
                data = await tg_response.read()
                async with session.put(upload_url, headers=headers, data=data) as bunny_response:
                    if bunny_response.status == 201:
                        await message.answer("✅ Uploaded to Bunny.net!")
                    else:
                        await message.answer("❌ Upload failed!")
                        logging.error(await bunny_response.text())
            else:
                await message.answer("❌ Failed to get file from Telegram.")

# Health check
async def health(request):
    return web.Response(text="✅ Bot is running!")

async def on_startup(app):
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/"
    await bot.set_webhook(webhook_url)
    logging.info(f"🚀 Webhook set to: {webhook_url}")

# App setup
app = web.Application()
app.router.add_get("/", health)
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
setup_application(app, dp, bot=bot)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))