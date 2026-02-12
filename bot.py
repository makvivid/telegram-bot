import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp import web
from datetime import datetime

# ================ НАСТРОЙКИ ================
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 488352806

if not API_TOKEN:
    raise ValueError("ERROR: BOT_TOKEN not set!")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ================ БАЗА ДАННЫХ ================
USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_user(user_id, username, full_name):
    users = load_users()
    for user in users:
        if user["id"] == user_id:
            return
    users.append({
        "id": user_id,
        "username": username,
        "full_name": full_name,
        "joined_date": str(datetime.now())
    })
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# ================ СОСТОЯНИЯ ================
class NewsletterStates(StatesGroup):
    waiting_for_text = State()

# ================ КЛАВИАТУРЫ ================
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
        [KeyboardButton(text="🧪 Химия для бассейнов"), KeyboardButton(text="🔧 Оборудование для бассейна")],
        [KeyboardButton(text="🚀 Комплекты для запуска"), KeyboardButton(text="🎯 Подбор под мой бассейн")],
        [KeyboardButton(text="🔙 Назад в главное меню")],
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

# ================ АДМИН-КЛАВИАТУРА ================
def get_admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📢 ОТПРАВИТЬ НОВОСТЬ"))
    kb.add(KeyboardButton("👥 СТАТИСТИКА"))
    kb.add(KeyboardButton("🔙 Назад в главное меню"))
    return kb

# ================ ПРОВЕРКА АДМИНА ================
def is_admin(user_id):
    return user_id == ADMIN_ID

# ================ СТАРТ ================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    save_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )
    
    welcome_text = (
        "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
        "📍 ДНР, г. Донецк, ул. Щорса 38\n"
        "📞 +7 949 321‑98‑00\n\n"
        "Выберите нужный раздел 👇"
    )
    
    await message.answer(welcome_text, reply_markup=main_kb, parse_mode="HTML")
    
    if is_admin(message.from_user.id):
        await message.answer("👑 ПАНЕЛЬ АДМИНИСТРАТОРА", reply_markup=get_admin_kb())

# ================ НАЗАД ================
@dp.message_handler(Text(equals="🔙 Назад в главное меню"))
async def back_to_main(message: types.Message):
    await cmd_start(message)

# ================ СТАТИСТИКА ================
@dp.message_handler(Text(equals="👥 СТАТИСТИКА"))
async def show_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    users = load_users()
    count = len(users)
    
    text = f"📊 <b>Статистика бота</b>\n\n👥 Всего пользователей: {count}"
    
    if count > 0:
        text += f"\n\n📅 Последние 5:\n"
        for user in users[-5:]:
            name = user['full_name'][:20]
            username = f"@{user['username']}" if user['username'] else "нет"
            text += f"• {name} {username}\n"
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_kb())

# ================ РАССЫЛКА ================
@dp.message_handler(Text(equals="📢 ОТПРАВИТЬ НОВОСТЬ"))
async def start_newsletter(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📝 <b>Напишите текст новости:</b>\n\n"
        "Это сообщение увидят ВСЕ пользователи бота.",
        parse_mode="HTML",
        reply_markup=back_kb
    )
    await NewsletterStates.waiting_for_text.set()

@dp.message_handler(state=NewsletterStates.waiting_for_text)
async def send_newsletter(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.finish()
        return
    
    if message.text == "🔙 Назад в главное меню":
        await state.finish()
        await cmd_start(message)
        return
    
    news_text = message.text
    users = load_users()
    
    status_msg = await message.answer(f"📤 Отправка новости {len(users)} пользователям...")
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await bot.send_message(
                user["id"],
                f"📢 <b>НОВОСТЬ ДОНАКВА</b>\n\n{news_text}",
                parse_mode="HTML"
            )
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}\n"
        f"👥 Всего: {len(users)}",
        parse_mode="HTML"
    )
    
    await state.finish()
    await cmd_start(message)

# ================ РАЗДЕЛ: АНАЛИЗ ВОДЫ ================
@dp.message_handler(Text(equals="🧪 Анализ воды"))
async def handle_analysis(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "🧪 АНАЛИЗ ВОДЫ"
    
    text = (
        "🧪 <b>Анализ воды</b>\n\n"
        "⏱ <b>Срок:</b> 2–5 рабочих дней\n"
        "💰 <b>Стоимость:</b> 3500 руб.\n\n"
        "📍 <b>Приём проб:</b>\n"
        "📅 Будние дни с 9:00 до 14:00\n"
        "🏢 ДНР, г. Донецк, ул. Щорса 38\n"
        "📞 +7 949 321‑98‑00"
    )
    await message.answer(text, reply_markup=analysis_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔄 Задать вопрос"))
async def handle_analysis_question(message: types.Message):
    await message.answer(
        "📝 Напишите ваш вопрос — я передам специалисту.",
        reply_markup=back_kb
    )

# ================ ПОДБОР СИСТЕМЫ ================
@dp.message_handler(Text(equals="💧 Подбор системы очистки"))
async def handle_select_system(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ"
    
    await message.answer(
        "💧 Выберите ваши условия:",
        reply_markup=select_system_kb,
        parse_mode="HTML"
    )

@dp.message_handler(Text(equals=["Питьевая вода для дома", "Квартира", "Частный дом", "Офис или бизнес", "Производство", "Просто интересуюсь"]))
async def handle_select_system_option(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ"
    
    option = message.text
    text = (
        f"✅ <b>{option}</b>\n\n"
        "📋 Опишите ситуацию:\n"
        "• Источник воды\n"
        "• Проблемы\n"
        "• Количество человек"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ БАССЕЙНЫ ================
@dp.message_handler(Text(equals="🏊 Химия и оборудование для бассейнов"))
async def handle_pool(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "🏊 БАССЕЙНЫ"
    
    await message.answer("🏊 Выберите раздел:", reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🧪 Химия для бассейнов"))
async def handle_pool_chemistry(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "🏊 БАССЕЙНЫ"
    
    text = (
        "🧪 <b>Химия для бассейнов</b>\n\n"
        "Опишите:\n"
        "• Какую химию нужно\n"
        "• Объём бассейна\n"
        "• Проблему"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔧 Оборудование для бассейна"))
async def handle_pool_equipment(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "🏊 БАССЕЙНЫ"
    
    text = (
        "🔧 <b>Оборудование для бассейна</b>\n\n"
        "Опишите:\n"
        "• Какое оборудование\n"
        "• Объём бассейна\n"
        "• Задачу"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🚀 Комплекты для запуска"))
async def handle_pool_startup(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "🏊 БАССЕЙНЫ"
    
    await message.answer(
        "🚀 Опишите объём и тип бассейна",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="🎯 Подбор под мой бассейн"))
async def handle_pool_custom(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "🏊 БАССЕЙНЫ"
    
    await message.answer(
        "🎯 Опишите ваш бассейн и задачу",
        reply_markup=back_kb
    )

# ================ О КОМПАНИИ ================
@dp.message_handler(Text(equals="ℹ️ О компании ДОНАКВА"))
async def handle_about(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "ℹ️ О КОМПАНИИ"
    
    text = (
        "🏢 <b>О компании ДОНАКВА</b>\n\n"
        "📍 г. Донецк, ул. Щорса, д. 38\n"
        "📞 +7 949 321‑98‑00\n"
        "🌐 www.donaqua.pro"
    )
    await message.answer(text, reply_markup=site_kb, parse_mode="HTML")

# ================ ПАРТНЁРСКАЯ ПРОГРАММА ================
@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА"
    
    await message.answer(
        "🤝 Выберите вашу сферу:",
        reply_markup=partner_kb,
        parse_mode="HTML"
    )

@dp.message_handler(Text(equals=["Сантехник / монтажник", "Архитектор / дизайнер", "Прораб / строитель", "Бурильщик скважин", "Другое"]))
async def handle_partner_option(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА"
    
    role = message.text
    await message.answer(
        f"✅ {role}\n\nОпишите сотрудничество",
        reply_markup=back_kb
    )

# ================ ЗАЯВКИ ================
@dp.message_handler(Text(equals="📩 Оставить заявку"))
async def handle_request(message: types.Message):
    # ЗАПОМИНАЕМ РАЗДЕЛ
    user_data[message.from_user.id] = "📩 ЗАЯВКА"
    
    await message.answer(
        "📋 Опишите вашу задачу.\nМожно прикрепить фото.",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="🌐 На сайт"))
async def handle_site(message: types.Message):
    await message.answer(
        "🌐 www.donaqua.pro",
        reply_markup=back_kb
    )

# ================ ХРАНИЛИЩЕ РАЗДЕЛОВ ================
user_data = {}  # user_id -> название раздела

# ================ ФОТО ================
@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    user = message.from_user
    photo = message.photo[-1]
    
    # Получаем раздел, если есть
    section = user_data.get(user.id, "📸 ФОТО")
    
    try:
        await bot.send_photo(
            ADMIN_ID,
            photo.file_id,
            caption=f"🔔 <b>{section}</b>\n\n👤 {user.full_name}\n📱 @{user.username}\n🆔 {user.id}\n💬 {message.caption or 'Без подписи'}",
            parse_mode="HTML"
        )
        await message.answer("✅ Спасибо!", reply_markup=main_kb)
    except:
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

# ================ ТЕКСТ ================
@dp.message_handler()
async def handle_text(message: types.Message):
    # Пропускаем команды
    if message.text.startswith('/'):
        return
    
    user = message.from_user
    
    # Админу не отправляем его же сообщения
    if is_admin(user.id):
        return
    
    # ПОЛУЧАЕМ РАЗДЕЛ ИЗ ХРАНИЛИЩА
    section = user_data.get(user.id, "📬 ОБЩАЯ ЗАЯВКА")
    
    # Очищаем, чтобы следующее сообщение не ушло в тот же раздел
    if user.id in user_data:
        del user_data[user.id]
    
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 <b>{section}</b>\n\n"
            f"👤 {user.full_name}\n"
            f"📱 @{user.username}\n"
            f"🆔 {user.id}\n\n"
            f"💬 {message.text}",
            parse_mode="HTML"
        )
        await message.answer("✅ Спасибо! Заявка отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

# ================ ВЕБ-СЕРВЕР ================
async def handle_web(request):
    return web.Response(text="🤖 Бот ДОНАКВА работает!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle_web)
    app.router.add_get('/health', handle_web)
    
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Веб-сервер запущен на порту {port}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await asyncio.Event().wait()

# ================ ЗАПУСК ================
async def main():
    print("🤖 Бот ДОНАКВА запущен")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print(f"👥 Всего пользователей: {len(load_users())}")
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    await asyncio.gather(
        dp.start_polling(),
        run_web_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
