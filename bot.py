import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from ftplib import FTP

# Bunny credentials
BUNNY_FTP_HOST = "storage.bunnycdn.com"
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_ZONE", "Ben-10")
BUNNY_USERNAME = os.getenv("BUNNY_USER", "Ben-10")
BUNNY_PASSWORD = os.getenv("BUNNY_PASSWORD", "your-password")

# Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")

logging.basicConfig(level=logging.INFO)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("Please send a video.")
        return

    file = await context.bot.get_file(video.file_id)
    file_name = video.file_name or "video.mp4"
    local_path = f"/tmp/{file_name}"

    await update.message.reply_text("⬇ Downloading from Telegram...")
    await file.download_to_drive(local_path)

    await update.message.reply_text("⬆ Uploading to Bunny.net...")

    try:
        ftp = FTP(BUNNY_FTP_HOST)
        ftp.login(BUNNY_USERNAME, BUNNY_PASSWORD)
        ftp.cwd(f"/{BUNNY_STORAGE_ZONE}")

        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR {file_name}", f)

        ftp.quit()
        await update.message.reply_text(f"✅ Uploaded to Bunny CDN!\nURL: https://{BUNNY_STORAGE_ZONE}.b-cdn.net/{file_name}")
    except Exception as e:
        await update.message.reply_text(f"❌ Upload failed: {e}")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.run_polling()
