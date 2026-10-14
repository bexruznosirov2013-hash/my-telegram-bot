import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

BOT_TOKEN = "8869344185:AAEoxcxhCm2mi9SPpLYmWKqkAQi5nf7UC6s"
GEMINI_API_KEY = "AQ.Ab8RN6LDVXUrqKAFJx44BR46-F2Y5rOjuKdLgrwT0lBSihWeyg"

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class QuizForm(StatesGroup):
    waiting_for_class = State()
    waiting_for_pages = State()

def get_classes_keyboard():
    buttons = []
    row = []
    for i in range(1, 12):
        row.append(InlineKeyboardButton(text=f"{i}-sinf", callback_data=f"class_{i}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! Texnologiya fanidan AI-Test generator botiga xush kelibsiz.\n\n"
        "Qaysi sinf Texnologiya kitobidan test tuzmoqchisiz? Tanlang:",
        reply_markup=get_classes_keyboard()
    )
    await state.set_state(QuizForm.waiting_for_class)

@dp.callback_query(F.data.startswith("class_"), QuizForm.waiting_for_class)
async def process_class(call: types.CallbackQuery, state: FSMContext):
    class_num = call.data.split("_")[1]
    await state.update_data(selected_class=class_num)
    
    await call.message.edit_text(
        f"Siz **{class_num}-sinf** Texnologiya kitobini tanladingiz.\n\n"
        f"Endi kitobning qaysi sahifalaridan test tuzay? (Masalan: `20-30` deb yozib yuboring):",
        parse_mode="Markdown"
    )
    await state.set_state(QuizForm.waiting_for_pages)

@dp.message(QuizForm.waiting_for_pages)
async def generate_quiz(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    selected_class = user_data.get("selected_class")
    pages = message.text

    wait_msg = await message.answer("Sun'iy intellekt darslik ma'lumotlarini tahlil qilib, 15 talik test tuzmoqda... Iltimos, kutib turing...")

    prompt = (
        f"Maktab darsligi: {selected_class}-sinf Texnologiya fani.\n"
        f"O'qilgan sahifalar: {pages}-betlar.\n"
        f"Topshiriq: Ushbu sinf va sahifalarga tegishli Texnologiya darsligi mavzulari va bilimlaridan kelib chiqib, "
        f"o'quvchini sinash uchun 15 ta ko'p tanlovli (A, B, C, D variantli) test tuzib ber. "
        f"Har bir savol ostida to'g'ri javobni ham ko'rsat. O'zbek tilida ravon bo'lsin."
    )

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        quiz_text = response.text
        await wait_msg.delete()
        
        if len(quiz_text) > 4000:
            for x in range(0, len(quiz_text), 4000):
                await message.answer(quiz_text[x:x+4000])
        else:
            await message.answer(f"**{selected_class}-sinf Texnologiya ({pages}-betlar) bo'yicha 15 talik test:**\n\n{quiz_text}", parse_mode="Markdown")

    except Exception as e:
        await wait_msg.edit_text(f"Xatolik yuz berdi: {e}")
    
    await state.clear()

# Render port talabini qondirish uchun kichik veb-server
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    # Veb-server va botni birga ishga tushirish
    await web_server()
    print("AI-Test Bot va Veb-server ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
