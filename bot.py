import os
import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import google.generativeai as genai

# ================= KONFIGURATSIYA =================
BOT_TOKEN = "8869344185:AAEoxcxhCm2mi9SPpLYmWKqkAQi5nf7UC6s"
GEMINI_API_KEY = "AQ.Ab8RN6K11AcJurYlVIVm8BCxj5Gh17xc1pBkG7pjNeh_gnMBBQ"  # <-- AI Studio'dan olgan yangi kalitingiz!

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

class QuizState(StatesGroup):
    waiting_for_pages = State()

# ================= HANDLERLAR =================

# /start va /restart buyruqlari
@router.message(Command("start", "restart"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(QuizState.waiting_for_pages)
    
    txt = (
        "Siz 7-sinf Texnologiya kitobini tanladingiz.\n\n"
        "Endi kitobning qaysi sahifalaridan test tuzay? (Masalan: 20-30 deb yozib yuboring):"
    )
    await message.answer(txt)

@router.message(QuizState.waiting_for_pages)
async def process_pages(message: Message, state: FSMContext):
    pages = message.text.strip()
    await state.clear()  # Xatolik va cheksiz qaytarilishning oldini olish uchun FSM holatini tozalaymiz
    
    await message.answer("⏳ Gemini AI test tayyorlamoqda, biroz kuting...")
    
    prompt = f"""
    Siz maktab o'qituvchisisiz. 7-sinf Texnologiya darsligining {pages}-sahifalari bo'yicha 3 ta ko'p tanlovli (A, B, C, D) test savoli tuzing. 
    Javoblardan biri to'g'ri bo'lsin va oxirida to'g'ri javoblarni ko'rsating.
    """
    
    try:
        response = model.generate_content(prompt)
        await message.answer(response.text)
    except Exception as e:
        await message.answer(f"⚠️ Xatolik yuz berdi. Gemini API kalitingizni tekshiring!\n\nXatolik matni: {e}")

# ================= AIOHTTP WEB SERVER (RENDER UCHUN) =================
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
    # Webhook hamda eski getUpdates so'rovlarini tozalab tashlash (Conflict harakatlarini to'xtatadi)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
