import os
import asyncio
import json
import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# ================= KONFIGURATSIYA =================
BOT_TOKEN = "8995479536:AAEkjDyAB_JsFmkQZ5jvEvmNaVxL897Dqi4"
GEMINI_API_KEY = "AQ.Ab8RN6KVvn9jWSaeXqO15La6LnGls9AXm5d1T5lZ1-iy1v1SUg"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

class QuizState(StatesGroup):
    choosing_subject = State()
    choosing_grade = State()
    choosing_count = State()
    playing_quiz = State()

# ================= MENYULAR =================

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Test Tuzishni Boshlash", callback_data="start_quiz")],
        [InlineKeyboardButton(text="ℹ️ Yordam / Help", callback_data="help_menu"), InlineKeyboardButton(text="📞 Aloqa", callback_data="contact_admin")]
    ])

def get_subjects_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Texnologiya", callback_data="sub_Texnologiya"), InlineKeyboardButton(text="📐 Matematika", callback_data="sub_Matematika")],
        [InlineKeyboardButton(text="📚 Ona tili", callback_data="sub_Ona tili"), InlineKeyboardButton(text="🧪 Biologiya", callback_data="sub_Biologiya")],
        [InlineKeyboardButton(text="⚡ Fizika", callback_data="sub_Fizika"), InlineKeyboardButton(text="🌍 Jahon Tarixi", callback_data="sub_Jahon Tarixi")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekiston Tarixi", callback_data="sub_O'zbekiston Tarixi"), InlineKeyboardButton(text="📐 Geometriya", callback_data="sub_Geometriya")],
        [InlineKeyboardButton(text="🎵 Musiqa", callback_data="sub_Musiqa"), InlineKeyboardButton(text="🇬🇧 Ingliz tili", callback_data="sub_Ingliz tili")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")]
    ])

def get_grades_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5-sinf", callback_data="grade_5"),
            InlineKeyboardButton(text="6-sinf", callback_data="grade_6"),
            InlineKeyboardButton(text="7-sinf", callback_data="grade_7")
        ],
        [
            InlineKeyboardButton(text="8-sinf", callback_data="grade_8"),
            InlineKeyboardButton(text="9-sinf", callback_data="grade_9"),
            InlineKeyboardButton(text="10-sinf", callback_data="grade_10")
        ],
        [
            InlineKeyboardButton(text="11-sinf", callback_data="grade_11")
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="start_quiz")]
    ])

def get_counts_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 ta", callback_data="count_5"),
            InlineKeyboardButton(text="10 ta", callback_data="count_10")
        ],
        [
            InlineKeyboardButton(text="15 ta", callback_data="count_15"),
            InlineKeyboardButton(text="20 ta", callback_data="count_20")
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="start_quiz")]
    ])

# ================= GEMINI API BILAN BOG'LANISH =================
async def generate_quiz_questions(subject: str, grade: str, count: str):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }
    
    prompt = f"""
    Siz professional maktab o'qituvchisisiz. {grade}-sinf "{subject}" fanidan o'quvchilar uchun {count} ta test tuzing.
    Javobni FAQAT quyidagi JSON formatida qaytaring, boshqa hech qanday so'z yoki markdown belgi yozmang:
    [
      {{
        "question": "Savol matni?",
        "options": ["Variant 1", "Variant 2", "Variant 3", "Variant 4"],
        "correct_index": 0
      }}
    ]
    "correct_index" — to'g'ri javobning "options" massividagi indeksi (0 dan 3 gacha). Variantlar aniq 4 ta bo'lsin.
    """
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                try:
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                    return json.loads(clean_text)
                except Exception as e:
                    print(f"Xatolik: {e}")
                    return None
            else:
                return None

# ================= HANDLERLAR =================

@router.message(Command("start", "restart"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✨ **Assalomu alaykum! Maktab fanlaridan viktorina (Quiz) botiga xush kelibsiz.**\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@router.message(Command("help"))
async def help_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "ℹ️ **Bot haqida ma'lumot (Help):**\n\n"
        "Ushbu bot maktab o'quvchilari va o'qituvchilari uchun mo'ljallangan. "
        "Siz istalgan fan va sinfni tanlab, xuddi @QuizBot kabi viktorina savollarini qabul qilishingiz mumkin.\n\n"
        "**Buyruqlar:**\n"
        "/start - Botni qayta ishga tushirish\n"
        "/restart - Asosiy menyuga qaytish\n"
        "/help - Yordam va ma'lumot olish",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "help_menu")
async def help_cb(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ **Bot haqida ma'lumot:**\n\n"
        "Ushbu bot maktab o'quvchilari va o'qituvchilari uchun mo'ljallangan. "
        "Siz istalgan fan va sinfni tanlab, xuddi @QuizBot kabi viktorina savollarini qabul qilishingiz mumkin.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "start_quiz")
async def start_quiz_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(QuizState.choosing_subject)
    await callback.message.edit_text(
        "📚 **Test tuzish uchun fanni tanlang:**",
        reply_markup=get_subjects_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✨ **Asosiy menyu:**",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "contact_admin")
async def contact_cb(callback: CallbackQuery):
    await callback.message.edit_text(
        "📞 **Aloqa:**\n\nSavol va takliflar bo'yicha administratorga murojaat qilishingiz mumkin.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("sub_"), QuizState.choosing_subject)
async def process_subject(callback: CallbackQuery, state: FSMContext):
    subject = callback.data.split("_", 1)[1]
    await state.update_data(subject=subject)
    await state.set_state(QuizState.choosing_grade)
    
    await callback.message.edit_text(
        f"✅ Tanlangan fan: **{subject}**\n\n🎓 Endi sinfni tanlang:",
        reply_markup=get_grades_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("grade_"), QuizState.choosing_grade)
async def process_grade(callback: CallbackQuery, state: FSMContext):
    grade = callback.data.split("_")[1]
    await state.update_data(grade=grade)
    await state.set_state(QuizState.choosing_count)
    
    data = await state.get_data()
    await callback.message.edit_text(
        f"✅ Fan: {data['subject']} | Sinf: {grade}-sinf\n\n🔢 Nechta test savoli kerak?",
        reply_markup=get_counts_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("count_"), QuizState.choosing_count)
async def process_count(callback: CallbackQuery, state: FSMContext):
    count = callback.data.split("_")[1]
    data = await state.get_data()
    subject = data['subject']
    grade = data['grade']
    
    await callback.message.edit_text(
        f"⏳ **Gemini AI** {grade}-sinf **{subject}** fanidan {count} ta viktorina savollarini tayyorlamoqda...",
        parse_mode="Markdown"
    )
    
    questions = await generate_quiz_questions(subject, grade, count)
    
    if not questions:
        await callback.message.answer(
            "⚠️ Savollarni yaratishda xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        return
    
    await callback.message.answer(f"🎉 **{grade}-sinf {subject} fanidan {len(questions)} ta test boshlandi!**")
    
    for q in questions:
        try:
            await bot.send_poll(
                chat_id=callback.message.chat.id,
                question=q["question"],
                options=q["options"],
                type="quiz",
                correct_option_id=q["correct_index"],
                is_anonymous=False
            )
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Poll yuborishda xato: {e}")
            
    await callback.message.answer(
        "✅ **Barcha testlar yakunlandi!**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yana test tuzish", callback_data="start_quiz")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="back_to_main")]
        ]),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

# ================= AIOHTTP WEB SERVER =================
async def handle_ping(request):
    return web.Response(text="Bot live holatda ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/health', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
