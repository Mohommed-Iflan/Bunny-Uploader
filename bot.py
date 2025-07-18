import os
import aiohttp
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import setup_application
from aiohttp import web

# Load from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE")       # e.g., myzone
BUNNY_STORAGE_API_KEY = os.getenv("BUNNY_STORAGE_API_KEY") # get from Bunny dashboard
BUNNY_HOSTNAME = "storage.bunnycdn.com"                    # Bunny hostname

if not TELEGRAM_TOKEN:
    raise Exception("❌ TELEGRAM_TOKEN environment variable not set.")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


@dp.message(F.text)
async def handle_direct_link(message: types.Message):
    url = message.text.strip()

    # Validate link
    if not url.startswith("https://") or "file_" not in url:
        await message.reply("❌ Please send a valid Telegram direct file link.")
        return

    filename = url.split("/")[-1]

    try:
        await message.reply("⬇️ Downloading from Telegram...")

        # Download the file from Telegram
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as tg_resp:
                if tg_resp.status != 200:
                    await message.reply(f"❌ Failed to download file from Telegram. Status code: {tg_resp.status}")
                    return
                file_data = await tg_resp.read()

        await message.reply("⬆️ Uploading to Bunny.net...")

        # Upload to Bunny.net
        upload_url = f"https://{BUNNY_HOSTNAME}/{BUNNY_STORAGE_ZONE}/{filename}"
        headers = {"AccessKey": BUNNY_STORAGE_API_KEY}

        async with aiohttp.ClientSession() as session:
            async with session.put(upload_url, data=file_data, headers=headers) as resp:
                if resp.status in [200, 201]:
                    bunny_stream_url = f"https://{BUNNY_STORAGE_ZONE}.b-cdn.net/{filename}"
                    await message.reply(f"✅ Uploaded successfully!\n\n🎬 Bunny URL: {bunny_stream_url}")
                else:
                    error_text = await resp.text()
                    await message.reply(f"❌ Upload failed: {resp.status}\n{error_text}")

    except Exception as e:
        logging.exception("Upload error")
        await message.reply(f"❌ An error occurred:\n{str(e)}")


# Webhook setup (for Railway)
async def on_startup(app: web.Application):
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        raise Exception("❌ WEBHOOK_URL not set")
    await bot.set_webhook(webhook_url)
    logging.info(f"🚀 Webhook set to: {webhook_url}")

app = web.Application()
app.on_startup.append(on_startup)
dp.startup.register(on_startup)
setup_application(app, dp, bot=bot)