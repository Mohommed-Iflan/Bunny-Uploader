import os
import aiohttp
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import setup_application
from aiohttp import web, ClientSession, ClientTimeout, ContentLengthError
from aiogram.types import BotCommand
from aiogram.enums.dice_emoji import DiceEmoji

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE")
BUNNY_STORAGE_API_KEY = os.getenv("BUNNY_STORAGE_API_KEY")
BUNNY_STORAGE_REGION = os.getenv("BUNNY_STORAGE_REGION", "de")
BUNNY_PULL_ZONE = os.getenv("BUNNY_PULL_ZONE")

if not all([TELEGRAM_TOKEN, BUNNY_STORAGE_ZONE, BUNNY_STORAGE_API_KEY, BUNNY_PULL_ZONE]):
    raise RuntimeError("❌ Missing required environment variables.")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(F.text)
async def handle_link(message: Message):
    text = message.text.strip()
    if "http" not in text or not text.lower().endswith(".mp4") and ".mp4 " not in text:
        await message.reply("❌ Format:\n<code>filename.mp4 https://your-link</code>")
        return

    try:
        filename, link = text.split(" ", 1)
        filename = filename.strip()
        link = link.strip()

        if not filename.endswith(".mp4") or not link.startswith("http"):
            raise ValueError("Invalid format.")

        logging.info(f"📩 Received: {link}")

        # Download file with aiohttp
        try:
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=1200)) as session:
                async with session.get(link) as response:
                    if response.status != 200:
                        raise Exception(f"Download failed: {response.status}")
                    data = await response.read()
        except ContentLengthError as e:
            await message.reply(f"❌ <b>Download failed:</b>\n<code>{str(e)}</code>")
            return
        except Exception as e:
            await message.reply(f"❌ <b>Download error:</b>\n<code>{str(e)}</code>")
            return

        # Upload to Bunny
        try:
            upload_url = f"https://storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}/{filename}"
            headers = {
                "AccessKey": BUNNY_STORAGE_API_KEY,
                "Content-Type": "application/octet-stream"
            }
            async with aiohttp.ClientSession() as session:
                async with session.put(upload_url, data=data, headers=headers) as resp:
                    if resp.status != 201:
                        raise Exception(f"Bunny upload failed: {await resp.text()}")
        except Exception as e:
            await message.reply(f"❌ <b>Upload error:</b>\n<code>{str(e)}</code>")
            return

        cdn_link = f"https://{BUNNY_PULL_ZONE}/{filename}"
        await message.reply(f"✅ <b>Uploaded Successfully</b>\n🎬 <code>{filename}</code>\n🔗 <a href=\"{cdn_link}\">Watch Now</a>")

    except ValueError:
        await message.reply("❌ <b>Invalid format.</b>\nSend as:\n<code>filename.mp4 https://link</code>")
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b>\n<code>{str(e)}</code>")

# Webhook setup
async def on_startup(app):
    await bot.set_webhook("https://bunny-uploader-production.up.railway.app/")

async def on_shutdown(app):
    await bot.delete_webhook()

def create_app():
    app = web.Application()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    setup_application(app, dp, bot=bot)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8000)