import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shazamio import Shazam
import yt_dlp

BOT_TOKEN = "8925547381:AAFzKWCQZAgwiddQSuR3TBJriMMR3gKIVnY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
shazam = Shazam()

# /start buyrug'i
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Salom! Men eng tezkor Media Downloader va Music Finder botman!\n\n"
        " Menga Instagram/YouTube havolasini yuboring yoki video/audio fayl tashlang!"
    )

# 1. Musiqani fayl yoki videodan aniqlash (Shazam funksiyasi)
@dp.message(F.voice | F.audio | F.video)
async def recognize_music(message: types.Message):
    msg = await message.answer("🔍 Qo'shiq aniqlanmoqda, kuting...")
    
    # Faylni serverga yuklab olish
    file_id = message.voice.file_id if message.voice else (message.audio.file_id if message.audio else message.video.file_id)
    file = await bot.get_file(file_id)
    file_path = f"downloads/{file.file_id}.mp3"
    
    os.makedirs("downloads", exist_ok=True)
    await bot.download_file(file.file_path, file_path)
    
    # Shazam orqali qidirish
    out = await shazam.recognize(file_path)
    os.remove(file_path) # Vaqtinchalik faylni o'chirish
    
    track = out.get('track')
    if track:
        title = track.get('title')
        subtitle = track.get('subtitle')
        await msg.edit_text(f"🎵 **Topildi:** {subtitle} - {title}\n\n ⬇️ Musiqa yuklanmoqda...")
        # Bu yerda yt-dlp orqali topilgan qo'shiqni MP3 qilib yuklab yuborish kodi bo'ladi
    else:
        await msg.edit_text("❌ Afsuski, musiqani aniqlab bo'lmadi.")

# 2. YouTube va Instagram videolarni sifat tanlovi bilan yuklash
@dp.message(F.text.contains("instagram.com") | F.text.contains("youtube.com") | F.text.contains("youtu.be"))
async def handle_links(message: types.Message):
    url = message.text.strip()
    
    # Inline tugmalarni shakllantirish (Sifatni tanlash)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 High Quality (1080p/720p)", callback_data=f"dl|best|{url}"),
            InlineKeyboardButton(text="📱 Low Quality (480p)", callback_data=f"dl|worst|{url}")
        ],
        [
            InlineKeyboardButton(text="🎵 Faqat MP3 (Audio)", callback_data=f"dl|audio|{url}")
        ]
    ])
    
    await message.answer(" Sifatni tanlang:", reply_markup=kb)

# Tugma bosilganda yuklab berish
@dp.callback_query(F.data.startswith("dl|"))
async def process_download(call: types.CallbackQuery):
    _, quality, url = call.data.split("|", 2)
    await call.message.edit_text("⚡️ Yuklanmoqda, iltimos kuting...")
    
    # yt-dlp sozlamalari
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
    }
    
    if quality == "audio":
        ydl_opts['format'] = 'bestaudio/best'
    elif quality == "best":
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        ydl_opts['format'] = 'worstvideo+worstaudio/worst'

    loop = asyncio.get_event_loop()
    
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename

    # Asinxron yuklab olish
    file_path = await loop.run_in_executor(None, download)
    
    # Telegramga faylni yuborish
    if quality == "audio":
        await call.message.answer_audio(types.FSInputFile(file_path))
    else:
        await call.message.answer_video(types.FSInputFile(file_path))
        
    os.remove(file_path) # Yuklab bo'lingach serverdan o'chirish

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
