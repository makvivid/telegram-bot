import asyncio
import os
import base64
import json
from io import BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup

# ================ НАСТРОЙКИ ================
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 488352806  # Твой Telegram ID

if not API_TOKEN:
    raise ValueError("ERROR: BOT_TOKEN not set in environment variables!")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ================ ФАЙЛ ДЛЯ ХРАНЕНИЯ ПОЛЬЗОВАТЕЛЕЙ ================
USERS_FILE = "users.json"

def load_users():
    """Загружает список пользователей из файла"""
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_user(user_id, username, full_name):
    """Сохраняет пользователя в файл"""
    users = load_users()
    
    # Проверяем, есть ли уже такой пользователь
    for user in users:
        if user["id"] == user_id:
            return
    
    # Добавляем нового пользователя
    users.append({
        "id": user_id,
        "username": username,
        "full_name": full_name,
        "joined_date": str(datetime.now())
    })
    
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# ================ СОСТОЯНИЯ ДЛЯ РАССЫЛКИ ================
class NewsletterStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirmation = State()

# ================ ЛОГОТИП - ПРЯМАЯ ССЫЛКА ================
# Используем прямую ссылку на логотип с твоего сайта
LOGO_URL = "https://donaqua.pro/wp-content/uploads/2021/04/logo-1.png"

async def send_logo(chat_id, caption, reply_markup=None, parse_mode="HTML"):
    """Отправляет логотип по URL"""
    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=LOGO_URL,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки логотипа по URL: {e}")
        # Пробуем отправить без логотипа
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except:
            pass
        return False

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

# ================ АДМИНСКАЯ КНОПКА ================
def get_admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📢 Отправить новость"))
    kb.add(KeyboardButton("👥 Статистика"))
    kb.add(KeyboardButton("🔙 Назад в главное меню"))
    return kb

# ================ ПРОВЕРКА НА АДМИНА ================
def is_admin(user_id):
    return user_id == ADMIN_ID

# ================ СТАРТ ================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Сохраняем пользователя в базу
    save_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )
    
    welcome_text = (
        "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
        "Мы — профессиональная команда специалистов по очистке воды, "
        "насосному оборудованию и бассейнам.\n\n"
        "🔹 20+ лет опыта\n"
        "🔹 1000+ реализованных проектов\n"
        "🔹 Индивидуальный подход\n\n"
        "📍 ДНР, г. Донецк, ул. Щорса 38\n"
        "📞 +7 949 321‑98‑00\n\n"
        "Выберите нужный раздел 👇"
    )
    
    # Отправляем с логотипом
    await send_logo(message.chat.id, welcome_text, main_kb, "HTML")
    
    # Если это админ - показываем админ-меню
    if is_admin(message.from_user.id):
        await message.answer("👑 Панель администратора", reply_markup=get_admin_kb())

# ================ НАЗАД ================
@dp.message_handler(Text(equals="🔙 Назад в главное меню"))
async def back_to_main(message: types.Message):
    await cmd_start(message)

# ================ СТАТИСТИКА (АДМИН) ================
@dp.message_handler(Text(equals="👥 Статистика"))
async def show_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    users = load_users()
    count = len(users)
    
    stats_text = f"📊 <b>Статистика бота</b>\n\n"
    stats_text += f"👤 Всего пользователей: {count}\n"
    
    if count > 0:
        stats_text += f"\n📅 Последние 5:\n"
        for user in users[-5:]:
            name = user['full_name'][:20]
            stats_text += f"• {name} (@{user['username']})\n"
    
    await message.answer(stats_text, parse_mode="HTML", reply_markup=get_admin_kb())

# ================ РАССЫЛКА (АДМИН) ================
@dp.message_handler(Text(equals="📢 Отправить новость"))
async def start_newsletter(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора.")
        return
    
    await message.answer(
        "📝 <b>Отправка новости</b>\n\n"
        "Напишите текст для рассылки.\n"
        "Это сообщение увидят ВСЕ пользователи бота.",
        parse_mode="HTML",
        reply_markup=back_kb
    )
    await NewsletterStates.waiting_for_text.set()

@dp.message_handler(state=NewsletterStates.waiting_for_text)
async def get_newsletter_text(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.finish()
        return
    
    if message.text == "🔙 Назад в главное меню":
        await state.finish()
        await cmd_start(message)
        return
    
    # Сохраняем текст
    await state.update_data(newsletter_text=message.text)
    
    # Кнопки подтверждения
    confirm_kb = InlineKeyboardMarkup(row_width=2)
    confirm_kb.add(
        InlineKeyboardButton("✅ Отправить всем", callback_data="send_newsletter"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_newsletter")
    )
    
    # Показываем предпросмотр
    users = load_users()
    preview_text = (
        f"📢 <b>Предпросмотр новости</b>\n\n"
        f"{message.text}\n\n"
        f"👥 Будет отправлено: <b>{len(users)} пользователям</b>\n\n"
        f"Отправить?"
    )
    
    await message.answer(preview_text, parse_mode="HTML", reply_markup=confirm_kb)
    await NewsletterStates.waiting_for_confirmation.set()

@dp.callback_query_handler(lambda c: c.data == "send_newsletter", state=NewsletterStates.waiting_for_confirmation)
async def send_newsletter(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    
    if not is_admin(callback_query.from_user.id):
        await state.finish()
        return
    
    data = await state.get_data()
    newsletter_text = data.get("newsletter_text")
    users = load_users()
    
    await bot.send_message(
        callback_query.from_user.id,
        f"📤 Начинаю рассылку {len(users)} пользователям..."
    )
    
    # Отправляем всем пользователям
    success = 0
    failed = 0
    
    for user in users:
        try:
            await bot.send_message(
                user["id"],
                f"📢 <b>Новость от ДОНАКВА</b>\n\n{newsletter_text}",
                parse_mode="HTML"
            )
            success += 1
            await asyncio.sleep(0.05)  # Защита от флуда
        except Exception as e:
            failed += 1
            print(f"Не удалось отправить пользователю {user['id']}: {e}")
    
    # Отчет админу
    report = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 Отправлено: {success}\n"
        f"❌ Ошибок: {failed}\n"
        f"👥 Всего: {len(users)}"
    )
    await bot.send_message(callback_query.from_user.id, report, parse_mode="HTML")
    
    await state.finish()
    await cmd_start(callback_query.message)

@dp.callback_query_handler(lambda c: c.data == "cancel_newsletter", state=NewsletterStates.waiting_for_confirmation)
async def cancel_newsletter(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id, "❌ Рассылка отменена")
    await state.finish()
    await bot.send_message(callback_query.from_user.id, "❌ Рассылка отменена.")
    await cmd_start(callback_query.message)

# ================ РАЗДЕЛ: АНАЛИЗ ВОДЫ ================
@dp.message_handler(Text(equals="🧪 Анализ воды"))
async def handle_analysis(message: types.Message):
    text = (
        "🧪 <b>Анализ воды</b>\n\n"
        "⏱ <b>Срок:</b> 2–5 рабочих дней\n"
        "💰 <b>Стоимость:</b> 3500 руб.\n\n"
        "📍 <b>Адрес:</b>\n"
        "ДНР, г. Донецк, ул. Щорса 38\n"
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
    await message.answer(
        "💧 Выберите ваши условия:",
        reply_markup=select_system_kb,
        parse_mode="HTML"
    )

@dp.message_handler(Text(equals=["Питьевая вода для дома", "Квартира", "Частный дом", "Офис или бизнес", "Производство", "Просто интересуюсь"]))
async def handle_select_system_option(message: types.Message):
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
    await message.answer("🏊 Выберите раздел:", reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🧪 Химия для бассейнов"))
async def handle_pool_chemistry(message: types.Message):
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
    await message.answer(
        "🚀 Опишите объём и тип бассейна",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="🎯 Подбор под мой бассейн"))
async def handle_pool_custom(message: types.Message):
    await message.answer(
        "🎯 Опишите ваш бассейн и задачу",
        reply_markup=back_kb
    )

# ================ О КОМПАНИИ ================
@dp.message_handler(Text(equals="ℹ️ О компании ДОНАКВА"))
async def handle_about(message: types.Message):
    text = (
        "🏢 <b>О компании ДОНАКВА</b>\n\n"
        "📍 г. Донецк, ул. Щорса, д. 38\n"
        "📞 +7 949 321‑98‑00\n"
        "🌐 www.donaqua.pro"
    )
    
    await send_logo(message.chat.id, text, site_kb, "HTML")

# ================ ПАРТНЁРСКАЯ ПРОГРАММА ================
@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    await message.answer(
        "🤝 Выберите вашу сферу:",
        reply_markup=partner_kb,
        parse_mode="HTML"
    )

@dp.message_handler(Text(equals=["Сантехник / монтажник", "Архитектор / дизайнер", "Прораб / строитель", "Бурильщик скважин", "Другое"]))
async def handle_partner_option(message: types.Message):
    role = message.text
    await message.answer(
        f"✅ {role}\n\nОпишите сотрудничество",
        reply_markup=back_kb
    )

# ================ ЗАЯВКИ ================
@dp.message_handler(Text(equals="📩 Оставить заявку"))
async def handle_request(message: types.Message):
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

# ================ ФОТО С РАЗДЕЛАМИ ================
@dp.message_handler(content_types=ContentType.PHOTO)
async def handle_photo(message: types.Message):
    user = message.from_user
    photo = message.photo[-1]
    
    # Определяем раздел
    section = "📸 Заявка с фото"
    
    try:
        await bot.send_photo(
            ADMIN_ID,
            photo.file_id,
            caption=f"{section}\n👤 {user.full_name} (@{user.username})\n💬 {message.caption or 'Без подписи'}"
        )
        await message.answer("✅ Спасибо!", reply_markup=main_kb)
    except:
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

# ================ ТЕКСТ С РАЗДЕЛАМИ ================
@dp.message_handler()
async def handle_text(message: types.Message):
    if message.text.startswith('/'):
        return
    
    # Определяем раздел по последнему сообщению
    section = "📬 Общая заявка"
    
    # Простое определение раздела по тексту
    text_lower = message.text.lower()
    if any(word in text_lower for word in ["анализ", "вода", "сдать", "проба"]):
        section = "🧪 Анализ воды"
    elif any(word in text_lower for word in ["бассейн", "химия", "хлор", "фильтр", "насос"]):
        section = "🏊 Бассейны"
    elif any(word in text_lower for word in ["систем", "очистк", "фильтр", "умягчение"]):
        section = "💧 Подбор системы"
    elif any(word in text_lower for word in ["партн", "сотрудничеств", "дилер"]):
        section = "🤝 Партнёрская программа"
    
    user = message.from_user
    
    try:
        await bot.send_message(
            ADMIN_ID,
            f"{section}\n\n👤 {user.full_name} (@{user.username}) id={user.id}\n💬 {message.text}"
        )
        await message.answer("✅ Спасибо! Заявка отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

# ================ RENDER ================
from aiohttp import web
from datetime import datetime

async def handle(request):
    return web.Response(text="🤖 Бот ДОНАКВА работает!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/health', handle)
    
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Веб-сервер запущен на порту {port}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await asyncio.Event().wait()

# ================ ЗАПУСК ================
async def main():
    print(f"🤖 Бот ДОНАКВА запущен")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print(f"🖼 Логотип: {LOGO_URL}")
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
