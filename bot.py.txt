import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Получаем токен из переменных окружения
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 488352806

if not API_TOKEN:
    raise ValueError("No BOT_TOKEN environment variable set!")

# Проверяем, что бот запускается правильно
print("Bot started with token:", API_TOKEN[:10] + "...")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Клавиатуры (оставляем как у тебя)
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧪 Анализ воды"), KeyboardButton(text="💧 Подбор системы очистки")],
        [KeyboardButton(text="🏊 Химия и оборудование для бассейнов")],
        [KeyboardButton(text="ℹ️ О компании ДОНАКВА")],
        [KeyboardButton(text="🤝 Партнёрская программа")],
        [KeyboardButton(text="📩 Оставить заявку")],
    ],
    resize_keyboard=True
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 Назад в главное меню")]],
    resize_keyboard=True
)

analysis_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Задать вопрос")],
        [KeyboardButton(text="🌐 На сайт")],
        [KeyboardButton(text="🔙 Назад в главное меню")],
    ],
    resize_keyboard=True
)

pool_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Химия для бассейнов"), KeyboardButton(text="Оборудование для бассейна")],
        [KeyboardButton(text="Комплекты для запуска"), KeyboardButton(text="Подбор под мой бассейн")],
        [KeyboardButton(text="Оставить заявку"), KeyboardButton(text="🔙 Назад в главное меню")],
    ],
    resize_keyboard=True
)

select_system_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Питьевая вода для дома")],
        [KeyboardButton(text="Квартира"), KeyboardButton(text="Частный дом")],
        [KeyboardButton(text="Офис или бизнес"), KeyboardButton(text="Производство")],
        [KeyboardButton(text="Просто интересуюсь")],
        [KeyboardButton(text="🔙 Назад в главное меню")],
    ],
    resize_keyboard=True
)

partner_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сантехник / монтажник")],
        [KeyboardButton(text="Архитектор / дизайнер")],
        [KeyboardButton(text="Прораб / строитель")],
        [KeyboardButton(text="Бурильщик скважин")],
        [KeyboardButton(text="Другое")],
        [KeyboardButton(text="🔙 Назад в главное меню")],
    ],
    resize_keyboard=True
)

site_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌐 На сайт")],
        [KeyboardButton(text="🔙 Назад в главное меню")],
    ],
    resize_keyboard=True
)

# Обработчики команд
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    text = (
        "ДОНАКВА — фильтры для воды, насосы, бассейны.\n\n"
        "Адрес магазина:\n"
        "ДНР, г. Донецк, ул. Щорса 38, магазин ДОНАКВА\n"
        "Телефон: +7 949 321‑98‑00\n\n"
        "Выберите нужный раздел:"
    )
    await message.answer(text, reply_markup=main_kb)

@dp.message_handler(Text(equals="🔙 Назад в главное меню"))
async def handle_back_to_main(message: types.Message):
    await cmd_start(message)

@dp.message_handler(Text(equals="🧪 Анализ воды"))
async def handle_analysis(message: types.Message):
    text = (
        "🧪 Анализ воды\n\n"
        "Мы проводим лабораторный анализ воды по вашему образцу.\n\n"
        "⏱ Срок выполнения: 2–5 рабочих дней.\n"
        "💰 Стоимость: 3500 руб.\n\n"
        "📍 Адрес:\n"
        "ДНР, г. Донецк, ул. Щорса 38, магазин ДОНАКВА\n"
        "Телефон: +7 949 321‑98‑00\n\n"
        "Как подготовить образец:\n"
        "• пластиковая бутылка 1–1,5 л\n"
        "• перед набором слейте воду 2–3 раза\n"
        "• наберите свежую воду без газа\n"
        "• плотно закройте бутылку\n\n"
        "После анализа мы объясним результаты и подскажем, что делать дальше."
    )
    await message.answer(text, reply_markup=analysis_kb)

@dp.message_handler(Text(equals="🔄 Задать вопрос"))
async def handle_analysis_question(message: types.Message):
    await message.answer(
        "Напишите ваш вопрос по воде одним сообщением — я передам его специалисту ДОНАКВА.",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="💧 Подбор системы очистки"))
async def handle_select_system(message: types.Message):
    await message.answer(
        "💧 Подбор системы очистки\n\nВыберите, для каких условий нужна очистка воды.",
        reply_markup=select_system_kb
    )

@dp.message_handler(Text(equals=["Питьевая вода для дома", "Квартира", "Частный дом", "Офис или бизнес", "Производство", "Просто интересуюсь"]))
async def handle_select_system_option(message: types.Message):
    option = message.text
    base = (
        "Опишите вашу ситуацию одним сообщением:\n"
        "• откуда вода\n"
        "• какие проблемы (запах, вкус, накипь, железо и т.п.)\n\n"
        "Я передам информацию специалисту ДОНАКВА."
    )
    await message.answer(f"Вы выбрали: {option}\n\n{base}", reply_markup=back_kb)

@dp.message_handler(Text(equals="🏊 Химия и оборудование для бассейнов"))
async def handle_pool(message: types.Message):
    await message.answer(
        "🏊 Химия и оборудование для бассейнов\n\nУ нас есть химия, фильтры, насосы и комплекты для запуска бассейна.",
        reply_markup=pool_kb
    )

@dp.message_handler(Text(equals=["Оставить заявку", "Подбор под мой бассейн"]))
async def handle_pool_request(message: types.Message):
    await message.answer(
        "Опишите ваш бассейн:\n• объём\n• тип\n• проблема или задача\n\nНапишите всё одним сообщением.",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="ℹ️ О компании ДОНАКВА"))
async def handle_about(message: types.Message):
    await message.answer(
        "ℹ️ О компании ДОНАКВА\n\nМы занимаемся очисткой воды, насосами и инженерными решениями.",
        reply_markup=site_kb
    )

@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    await message.answer(
        "🤝 Партнёрская программа\n\nВыберите вашу сферу:",
        reply_markup=partner_kb
    )

@dp.message_handler(Text(equals=["Сантехник / монтажник", "Архитектор / дизайнер", "Прораб / строитель", "Бурильщик скважин", "Другое"]))
async def handle_partner_option(message: types.Message):
    role = message.text
    await message.answer(
        f"Вы выбрали: {role}\n\nОпишите, чем вы занимаетесь и какой формат сотрудничества интересен.",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="📩 Оставить заявку"))
async def handle_request(message: types.Message):
    await message.answer(
        "Опишите вашу задачу одним сообщением. Можете прикрепить фото.",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="🌐 На сайт"))
async def handle_site(message: types.Message):
    await message.answer("Наш сайт: www.donaqua.pro", reply_markup=back_kb)

# Обработчик всех остальных сообщений
@dp.message_handler()
async def handle_free_text(message: types.Message):
    # Отправляем заявку админу
    user = message.from_user
    user_info = f"{user.full_name} (@{user.username}) id={user.id}"
    
    header = "Новая заявка от пользователя бота ДОНАКВА:\n\n"
    text = header + f"От: {user_info}\n\nТекст:\n{message.text}"
    
    await bot.send_message(chat_id=ADMIN_ID, text=text)
    
    await message.answer(
        "Спасибо! Ваша заявка отправлена. Мы свяжемся с вами в ближайшее время.",
        reply_markup=main_kb
    )

if __name__ == "__main__":
    # Запуск бота
    asyncio.run(dp.start_polling())

