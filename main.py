import os
from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot 24/7 aktivdir!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()
import os
import re
import json
import asyncio
from datetime import date
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# BotFather-dən aldığın tokeni dırnaqların içinə yaz
TOKEN = "TOKEN = "8806349684:AAEHLZMVYODXXBGEmdXba6Ik3Mbm2IBF1Ls"

DAILY_LIMIT = 15              # hər nəfərə gündə neçə mahnı
MAX_SIZE = 50 * 1024 * 1024   # Telegram bot limiti: 50 MB
USAGE_FILE = "usage.json"     # gündəlik limitlər
CACHE_FILE = "cache.json"     # video id -> Telegram file_id (sürət üçün)


# ---------- Limit ----------
def load_usage():
    try:
        with open(USAGE_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        data = {}
    if data.get("date") != str(date.today()):
        data = {"date": str(date.today()), "users": {}}
    return data


def save_usage(data):
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f)


def used_today(user_id):
    return load_usage()["users"].get(str(user_id), 0)


def add_usage(user_id):
    data = load_usage()
    data["users"][str(user_id)] = data["users"].get(str(user_id), 0) + 1
    save_usage(data)


# ---------- Cache ----------
def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def cache_get(video_id):
    return load_cache().get(video_id)


def cache_set(video_id, file_id):
    data = load_cache()
    data[video_id] = file_id
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def extract_video_id(url):
    m = re.search(
        r"(?:youtu\.be/|v=|/shorts/|/embed/)([A-Za-z0-9_-]{11})", url
    )
    return m.group(1) if m else None


# ---------- Endirmə ----------
def download_audio(url):
    opts = {
        # 128 kbps-ə qədər: fayl kiçikdir, daha tez endirilir və göndərilir
        "format": (
            "bestaudio[ext=m4a][abr<=128]/bestaudio[abr<=128]/"
            "bestaudio[ext=m4a]/bestaudio"
        ),
        "outtmpl": "%(id)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
    return path, info


# ---------- Komandalar ----------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Salam! Mənə YouTube linki göndər, mahnını audio kimi qaytarım.\n"
        f"Gündəlik limit: {DAILY_LIMIT} mahnı. Qalan hüququnu görmək üçün /limit yaz."
    )


async def limit_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    left = DAILY_LIMIT - used_today(update.effective_user.id)
    await update.message.reply_text(f"Bu gün qalan hüququn: {max(left, 0)}/{DAILY_LIMIT}")


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()

    if "youtu" not in url:
        await update.message.reply_text("Zəhmət olmasa YouTube linki göndər.")
        return

    if used_today(user_id) >= DAILY_LIMIT:
        await update.message.reply_text(
            f"Gündəlik limitin ({DAILY_LIMIT}) bitdi. Sabah yenidən yoxla 🙂"
        )
        return

    # 1) Cache yoxla: varsa dərhal göndər, endirmə yoxdur
    video_id = extract_video_id(url)
    if video_id:
        file_id = cache_get(video_id)
        if file_id:
            try:
                await update.message.reply_audio(file_id)
                add_usage(user_id)
                return
            except Exception:
                pass  # köhnə/yanlış file_id: normal endirməyə keç

    # 2) Cache-də yoxdursa endir
    msg = await update.message.reply_text("Yüklənir... ⏳")
    path = None
    try:
        path, info = await asyncio.to_thread(download_audio, url)

        if os.path.getsize(path) > MAX_SIZE:
            await msg.edit_text("Fayl 50 MB-dan böyükdür, göndərə bilmirəm.")
            return

        with open(path, "rb") as f:
            sent = await update.message.reply_audio(
                f,
                title=info.get("title"),
                performer=info.get("uploader"),
                duration=info.get("duration"),
            )

        # sonrakı dəfə üçün cache-ə yaz
        if sent.audio:
            cache_set(info.get("id") or video_id, sent.audio.file_id)

        add_usage(user_id)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"Xəta baş verdi: {str(e)[:200]}")
    finally:
        if path and os.path.exists(path):
            os.remove(path)


def main():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .concurrent_updates(True)
        .connect_timeout(30)
        .read_timeout(120)
        .write_timeout(180)
        .pool_timeout(30)
        
        
        # bir nəfər gözləyəndə digərləri bloklanmasın
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("limit", limit_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot işləyir...")
    app.run_polling()


if __name__ == "__main__":
    main()
