import os
import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import google.generativeai as genai

# ================= KONFIGURATSIYA =================
BOT_TOKEN = "8878301263:AAE4HbQGUPrQld6xcpdEh19y2ZdaZkpjay8"
GEMINI_API_KEY = "AQ.Ab8RN6LsBVCO1yE-rTAviimhEZJgvzAFLWCceUpEFMW_DymmbQ"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

class QuizState(StatesGroup):
    choosing_subject = State()
    choosing_grade = State()
    choosing_count = State()
    generating = State()

# Fanlar menyusi (Texnologiya va boshqa barcha fanlar)
def get_subjects_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Texnologiya", callback_data="sub_Texnologiya"), InlineKeyboardButton(text="📐 Matematika", callback_data="sub_Matematika")],
        [InlineKeyboardButton(text="📚 Ona tili", callback_data="sub_Ona tili"), InlineKeyboardButton(text="🧪 Biologiya", callback_data="sub_Biologiya")],
        [InlineKeyboardButton(text="⚡ Fizika", callback_data="sub_Fizika"), InlineKeyboardButton(text="🌍 Jahon Tarixi", callback_data="sub_Jahon Tarixi")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekiston Tarixi", callback_data="sub_O'zbekiston Tarixi"), InlineKeyboardButton(text="📐 Geometriya", callback_data="sub_Geometriya")],
        [InlineKeyboardButton(text="🎵 Musiqa", callback_data="sub_Musiqa"), InlineKeyboardButton(text="🇬🇧 Ingliz tili", callback_data="sub_Ingliz tili")]
    ])
    return keyboard

def get_grades_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
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
        ]
    ])
    return keyboard

def get_counts_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 ta", callback_data="count_5"),
            InlineKeyboardButton(text="10 ta", callback_data="count_10")
        ],
        [
            InlineKeyboardButton(text="15 ta", callback_data="count_15"),
            InlineKeyboardButton(text="20 ta", callback_data="count_20")
        ]
    ])
    return keyboard

@router.message(Command("start", "restart"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(QuizState.choosing_subject)
    await message.answer(
        "👋 Assalomu alaykum! Maktab fanlaridan sun'iy intellekt yordamida test tuzuvchi botga xush kelibsiz.\n\n"
        "Quyidagi fanlardan birini tanlang:",
        reply_markup=get_subjects_keyboard()
    )

@router.callback_query(F.data.startswith("sub_"), QuizState.choosing_subject)
async def process_subject(callback: CallbackQuery, state: FSMContext):
    subject = callback.data.split("_", 1)[1]
    await state.update_data(subject=subject)
    await state.set_state(QuizState.choosing_grade)
    
    await callback.message.edit_text(
        f"✅ Tanlangan fan: **{subject}**\n\nEndi o'quvchi sinfini tanlang:",
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
        f"✅ Fan: {data['subject']} | Sinf: {grade}-sinf\n\nNechta test savoli tuzish kerak?",
        reply_markup=get_counts_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("count_"), QuizState.choosing_count)
async def process_count(callback: CallbackQuery, state: FSMContext):
    count = callback.data.split("_")[1]
    await state.update_data(count=count)
    await state.set_state(QuizState.generating)
    
    data = await state.get_data()
    subject = data['subject']
    grade = data['grade']
    
    await callback.message.edit_text(f"⏳ Gemini AI {grade}-sinf **{subject}** fanidan {count} ta test tayyorlamoqda, biroz kuting...", parse_mode="Markdown")
    
    prompt = f"""
    Siz professional maktab o'qituvchisisiz. 
    {grade}-sinf "{subject}" fanidan o'quvchilar uchun {count} ta ko'p tanlovli (A, B, C, D variantli) test savolini tuzing.
    Har bir savol ostida variantlar aniq ko'rsatilsin.
    Testning oxirida barcha savollarning to'g'ri javoblarini kalit shaklida va qisqacha tushuntirishi bilan birga aniq yozib bering.
    O'zbek tilida mukammal va tushunarli formatda chiqaring.
    """
    
    try:
        response = model.generate_content(prompt)
        test_text = response.text
        
        if len(test_text) > 4000:
            for i in range(0, len(test_text), 4000):
                await callback.message.answer(test_text[i:i+4000])
        else:
            await callback.message.answer(test_text)
            
        await callback.message.answer(
            "Yangi test tuzish uchun tugmani bosing:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Yana test tuzish", callback_data="restart_quiz")]
            ])
        )
    except Exception as e:
        await callback.message.answer(f"⚠️ Xatolik yuz berdi: {e}")
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "restart_quiz")
async def restart_inline(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(QuizState.choosing_subject)
    await callback.message.answer(
        "Quyidagi fanlardan birini tanlang:",
        reply_markup=get_subjects_keyboard()
    )
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
