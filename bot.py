import asyncio
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

# Зчитуємо токен із змінних середовища Render
TOKEN = os.getenv("8959212221:AAG5LzqxVFJY8mZ42vjgmryntEg04e3Rzkw")
ADMIN_PASSWORD = "1488"  # Секретний пароль для доступу до адмін-панелі

router = Router()
subscribers_set = set()


class AdminAuth(StatesGroup):
    waiting_for_admin_password = State()
    admin_logged_in = State()


def get_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔐 Увійти в адмін-панель")]],
        resize_keyboard=True,
    )


def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Зробити розсилку всім")],
            [KeyboardButton(text="📊 Кількість користувачів")],
            [KeyboardButton(text="🚪 Вийти з адмін-панелі")],
        ],
        resize_keyboard=True,
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    subscribers_set.add(user_id)
    await state.clear()
    await message.answer(
        "Привіт! Дякую, що зайшов за посиланням.",
        reply_markup=get_user_keyboard(),
    )


@router.message(F.text == "🔐 Увійти в адмін-панель")
async def ask_admin_password(message: Message, state: FSMContext):
    await state.set_state(AdminAuth.waiting_for_admin_password)
    await message.answer(
        "🔒 Введи секретний пароль адміністратора:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AdminAuth.waiting_for_admin_password)
async def check_admin_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.set_state(AdminAuth.admin_logged_in)
        await message.answer(
            "✅ Успішно! Панель адміністратора розблоковано.",
            reply_markup=get_admin_keyboard(),
        )
    else:
        await state.clear()
        await message.answer(
            "❌ Невірний пароль! Доступ заборонено.",
            reply_markup=get_user_keyboard(),
        )


@router.message(AdminAuth.admin_logged_in, F.text == "🚪 Вийти з адмін-панелі")
async def logout_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚪 Ви вийшли з адмін-панелі.", reply_markup=get_user_keyboard())


@router.message(AdminAuth.admin_logged_in, F.text == "📊 Кількість користувачів")
async def check_users_count(message: Message):
    await message.answer(f"👥 Кількість користувачів, які запустили бота: {len(subscribers_set)}")


@router.message(AdminAuth.admin_logged_in, F.text == "📢 Зробити розсилку всім")
async def broadcast_prompt(message: Message):
    await message.answer(
        "Щоб зробити розсилку, напиши команду так:\n\n"
        "`/broadcast Твій текст тут`",
        parse_mode="Markdown",
    )


@router.message(AdminAuth.admin_logged_in, Command("broadcast"))
async def send_broadcast(message: Message):
    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        await message.answer("❌ Напиши текст після команди `/broadcast`.", parse_mode="Markdown")
        return

    success_count = 0
    fail_count = 0

    for user_id in subscribers_set:
        try:
            await message.bot.send_message(user_id, text_to_send)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            fail_count += 1
            print(f"Помилка для {user_id}: {e}")

    await message.answer(
        f"✅ **Розсилку завершено!**\n\n• Надіслано: {success_count}\n• Помилок: {fail_count}",
        parse_mode="Markdown",
    )


async def main():
    if not TOKEN:
        print("Помилка: не знайдено BOT_TOKEN!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    print("Бот запущено успішно!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())