import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("Помилка: не знайдено BOT_TOKEN!")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

subscribers_set = set()
ADMIN_PASSWORD = "1488"

class AdminAuth(StatesGroup):
    waiting_for_password = State()
    waiting_for_broadcast_text = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    subscribers_set.add(message.from_user.id)
    await message.answer("Привіт! Ви успішно підписалися на розсилку.")

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    await message.answer("Будь ласка, введіть пароль адміністратора:")
    await state.set_state(AdminAuth.waiting_for_password)

@dp.message(AdminAuth.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await message.answer("Пароль вірний! Введіть текст для розсилки:")
        await state.set_state(AdminAuth.waiting_for_broadcast_text)
    else:
        await message.answer("Невірний пароль! Доступ заборонено.")
        await state.clear()

@dp.message(AdminAuth.waiting_for_broadcast_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    text = message.text
    count = 0
    for user_id in list(subscribers_set):
        try:
            await bot.send_message(chat_id=user_id, text=text)
            count += 1
        except Exception:
            pass
    await message.answer(f"Розсилку завершено! Надіслано користувачам: {count}")
    await state.clear()

# Фіктивний веб-сервер для Render
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

