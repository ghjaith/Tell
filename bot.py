import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import yt_dlp

# تم وضع التوكن والأيدي الخاص بك هنا تلقائياً
TOKEN = "9168273160:AAEo9QvHc9lxON7hjgLzqQtUtZVpew-eh4Q"
ADMIN_ID = 1658759419
CHANNEL_USERNAME = "@YourChannelUsername"  # ضع معرف قناتك هنا لاحقاً للاشتراك الإجباري (مثلاً @StoreGhai)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users_db = set()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

async def check_sub(user_id: int) -> bool:
    if not CHANNEL_USERNAME or CHANNEL_USERNAME == "@YourChannelUsername":
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        pass
    return False

def sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 اشترك في القناة أولاً", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(text="✅ تحققت من الاشتراك", callback_data="check_subscription")]
    ])

@dp.callback_query(F.data == "check_subscription")
async def verify_sub(callback: CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.edit_text("✅ شكراً لاشتراكك! يمكنك الآن استخدام البوت بكل مرونة.\n\nأرسل /start للبدء.")
    else:
        await callback.answer("❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    users_db.add(user_id)
    
    if not await check_sub(user_id):
        await message.answer("⚠️ عذراً، يجب عليك الاشتراك في قناة البوت لتتمكن من استخدامه.", reply_markup=sub_keyboard())
        return

    if user_id == ADMIN_ID:
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 إرسال رسالة للكل", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📊 إحصائيات البوت", callback_data="admin_stats")],
            [InlineKeyboardButton(text="⚙️ إعدادات البوت", callback_data="admin_settings")]
        ])
        await message.answer(f"مرحباً بك يا مطوري العزيز! 👑\nهذه لوحة التحكم الخاصة بك:", reply_markup=admin_keyboard)
        return

    await message.answer(
        "مرحباً بك في بوت التحميل الشامل! 🚀\n\n"
        "أرسل لي:\n"
        "• يوزرنيم إنستغرام لجلب المعلومات والستوريات والهايلايت.\n"
        "• رابط Reels انستا أو TikTok أو YouTube لتحميله مباشرة."
    )

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("✍️ أرسل الآن الرسالة التي تريد إذاعتها لجميع المستخدمين:")
    await state.set_state(BroadcastState.waiting_for_message)

@dp.message(BroadcastState.waiting_for_message)
async def execute_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    sent_count, failed_count = 0, 0
    status_msg = await message.answer("⏳ جاري بدء الإذاعة...")
    
    for uid in users_db:
        try:
            await message.copy_to(chat_id=uid)
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed_count += 1
            
    await status_msg.edit_text(f"✅ تمت الإذاعة بنجاح!\n- تم الإرسال إلى: {sent_count}\n- فشل: {failed_count}")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer(f"📊 إحصائيات البوت:\n- عدد المستخدمين المسجلين: {len(users_db)}")

@dp.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("⚙️ إعدادات البوت:\n- البوت يعمل 24/7 عبر السيرفر السحابي.\n- قناة الاشتراك: " + CHANNEL_USERNAME)

@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    if not await check_sub(user_id):
        await message.answer("⚠️ يرجى الاشتراك في القناة أولاً لتتمكن من استخدام البوت:", reply_markup=sub_keyboard())
        return

    text = message.text.strip()
    
    if "youtube.com" in text or "youtu.be" in text:
        msg = await message.answer("🔍 جاري التحقق من رابط اليوتيوب...")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 فيديو (MP4)", callback_data=f"yt_vid_{text}"),
                InlineKeyboardButton(text="🎵 ملف صوتي (MP3)", callback_data=f"yt_audio_{text}")
            ]
        ])
        await msg.edit_text("✅ رابط صحيح! اختر صيغة التحميل:", reply_markup=keyboard)
        
    elif "tiktok.com" in text or "instagram.com/reel" in text:
        await message.answer("⏳ جاري تحميل المقطع...")
        try:
            ydl_opts = {'format': 'best', 'outtmpl': 'downloads/%(id)s.%(ext)s', 'socket_timeout': 10}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)
            await message.answer_video(FSInputFile(filename), caption="تم التحميل بواسطة البوت ✨")
            os.remove(filename)
        except Exception:
            await message.answer("❌ حدث خطأ أثناء التحميل: تأكد أن الرابط عام.")
            
    elif not text.startswith("http"):
        username = text.replace("@", "").strip()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 عرض الستوري", callback_data=f"story_{username}"),
                InlineKeyboardButton(text="📂 عرض الهايلات", callback_data=f"highlights_{username}")
            ]
        ])
        await message.answer(f"👤 **معلومات الحساب:**\n- اليوزر: @{username}\n\nاختر ما ترغب بعرضه:", reply_markup=keyboard)
    else:
        await message.answer("❓ لم أفهم هذا الرابط.")

@dp.callback_query(F.data.startswith("yt_vid_"))
async def download_yt_video(callback: CallbackQuery):
    url = callback.data.replace("yt_vid_", "")
    await callback.message.edit_text("⏳ جاري تحميل الفيديو من يوتيوب...")
    try:
        ydl_opts = {'format': 'best[ext=mp4]', 'outtmpl': 'downloads/%(id)s.%(ext)s'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        await callback.message.answer_video(FSInputFile(filename))
        os.remove(filename)
    except Exception:
        await callback.message.answer("❌ فشل تحميل الفيديو.")

@dp.callback_query(F.data.startswith("yt_audio_"))
async def download_yt_audio(callback: CallbackQuery):
    url = callback.data.replace("yt_audio_", "")
    await callback.message.edit_text("⏳ جاري استخراج الصوت...")
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'outtmpl': 'downloads/%(id)s.%(ext)s'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
        await callback.message.answer_audio(FSInputFile(filename))
        os.remove(filename)
    except Exception:
        await callback.message.answer("❌ فشل تحميل الصوت.")

async def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
      
