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
    # Сохраняем пользователя
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
    
    await message.answer(welcome_text, reply_markup=main_kb, parse_mode="HTML")
    
    # Если это админ - показываем админ-меню
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
    text = (
        "🧪 <b>Анализ воды</b>\n\n"
        "Анализ воды — первый и правильный шаг в подборе водоочистного оборудования.\n"
        "На основе химического и бактериологического анализа мы подберем оптимальное решение.\n\n"
        "⏱ <b>Срок:</b> 2–5 рабочих дней\n"
        "💰 <b>Стоимость:</b> 3500 руб.\n\n"
        "📍 <b>Приём проб:</b>\n"
        "📅 Будние дни с 9:00 до 14:00\n"
        "🏢 ДНР, г. Донецк, ул. Щорса 38, магазин ДОНАКВА\n"
        "📞 +7 949 321‑98‑00\n\n"
        "📋 <b>Как подготовить пробу:</b>\n"
        "• Бутылка 1–1,5 л (чистая, пластик)\n"
        "• Слить воду 2–3 минуты\n"
        "• Набрать свежую воду без газа\n"
        "• Плотно закрыть\n\n"
        "После анализа мы подробно объясним результаты и предложим решение!"
    )
    await message.answer(text, reply_markup=analysis_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔄 Задать вопрос"))
async def handle_analysis_question(message: types.Message):
    await message.answer(
        "📝 Напишите ваш вопрос по воде или анализу — "
        "я передам его специалисту ДОНАКВА.",
        reply_markup=back_kb
    )

# ================ ПОДБОР СИСТЕМЫ ОЧИСТКИ ================
@dp.message_handler(Text(equals="💧 Подбор системы очистки"))
async def handle_select_system(message: types.Message):
    text = (
        "💧 <b>Подбор системы очистки воды</b>\n\n"
        "Мы предлагаем:\n"
        "• Мембранные технологии (обратный осмос)\n"
        "• Фильтрация и обезжелезивание\n"
        "• Умягчение и химическая очистка\n"
        "• Безреагентные системы\n\n"
        "Выберите ваши условия:"
    )
    await message.answer(text, reply_markup=select_system_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Питьевая вода для дома", "Квартира", "Частный дом", "Офис или бизнес", "Производство", "Просто интересуюсь"]))
async def handle_select_system_option(message: types.Message):
    option = message.text
    text = (
        f"✅ <b>Вы выбрали:</b> {option}\n\n"
        "📋 <b>Опишите ситуацию:</b>\n"
        "• Источник воды (скважина, колодец, водопровод)\n"
        "• Проблемы (запах, вкус, накипь, ржавчина, мутность)\n"
        "• Количество человек/сотрудников\n"
        "• Примерный расход воды\n\n"
        "Я передам специалисту для подбора оптимального решения!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ БАССЕЙНЫ ================
@dp.message_handler(Text(equals="🏊 Химия и оборудование для бассейнов"))
async def handle_pool(message: types.Message):
    text = (
        "🏊 <b>Химия и оборудование для бассейнов</b>\n\n"
        "👇 <b>Выберите раздел:</b>"
    )
    await message.answer(text, reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🧪 Химия для бассейнов"))
async def handle_pool_chemistry(message: types.Message):
    text = (
        "🧪 <b>Химия для бассейнов</b>\n\n"
        "Опишите, какая химия вам нужна:\n\n"
        "• <b>Тип химии</b> (хлор, бром, альгицид, pH)\n"
        "• <b>Объём бассейна</b> (в м³)\n"
        "• <b>Проблема</b> (зелёная вода, мутная, запах)\n\n"
        "📌 <i>Пример: «Хлор в таблетках для бассейна 25 м³, зелёная вода»</i>"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔧 Оборудование для бассейна"))
async def handle_pool_equipment(message: types.Message):
    text = (
        "🔧 <b>Оборудование для бассейна</b>\n\n"
        "Опишите, что нужно:\n\n"
        "• <b>Тип оборудования</b> (фильтр, насос, нагреватель)\n"
        "• <b>Объём бассейна</b> (в м³)\n"
        "• <b>Задача</b> (ремонт, замена, новый монтаж)\n\n"
        "📌 <i>Пример: «Песочный фильтр для бассейна 35 м³, старый сломался»</i>"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🚀 Комплекты для запуска"))
async def handle_pool_startup(message: types.Message):
    text = (
        "🚀 <b>Комплекты для запуска бассейна</b>\n\n"
        "Опишите ваш бассейн:\n\n"
        "• <b>Объём</b> (в м³)\n"
        "• <b>Тип</b> (новый/после зимы)\n\n"
        "📌 <i>Пример: «Запуск бассейна 45 м³, песочный фильтр»</i>"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🎯 Подбор под мой бассейн"))
async def handle_pool_custom(message: types.Message):
    text = (
        "🎯 <b>Индивидуальный подбор</b>\n\n"
        "Опишите вашу ситуацию:\n\n"
        "• <b>Объём бассейна</b> (м³)\n"
        "• <b>Тип</b> (частный/общественный)\n"
        "• <b>Что нужно</b> (химия/оборудование/всё вместе)\n"
        "• <b>Бюджет</b>\n\n"
        "📌 <i>Пример: «Бассейн 60 м³, частный. Нужен насос и дозация хлора. Бюджет до 150 000 руб.»</i>"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ О КОМПАНИИ ================
@dp.message_handler(Text(equals="ℹ️ О компании ДОНАКВА"))
async def handle_about(message: types.Message):
    text = (
        "🏢 <b>О компании ДОНАКВА</b>\n\n"
        "Высококвалифицированные специалисты выполняют:\n"
        "• Подбор оборудования для очистки воды\n"
        "• Монтаж и пусконаладку\n"
        "• Сервисное и гарантийное обслуживание\n\n"
        "📍 <b>Адрес:</b> г. Донецк, ул. Щорса, д. 38\n"
        "📞 <b>Телефон:</b> +7 949 321‑98‑00\n"
        "🌐 <b>Сайт:</b> www.donaqua.pro"
    )
    await message.answer(text, reply_markup=site_kb, parse_mode="HTML")

# ================ ПАРТНЁРСКАЯ ПРОГРАММА ================
@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    text = (
        "🤝 <b>Партнёрская программа ДОНАКВА</b>\n\n"
        "🎯 <b>Для кого:</b>\n"
        "• Сантехники и монтажники\n"
        "• Архитекторы и дизайнеры\n"
        "• Прорабы и строители\n"
        "• Бурильщики скважин\n\n"
        "✅ <b>Что предлагаем:</b>\n"
        "• Выгодные условия\n"
        "• Техническая поддержка\n"
        "• Обучение\n\n"
        "Выберите вашу сферу:"
    )
    await message.answer(text, reply_markup=partner_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Сантехник / монтажник", "Архитектор / дизайнер", "Прораб / строитель", "Бурильщик скважин", "Другое"]))
async def handle_partner_option(message: types.Message):
    role = message.text
    text = (
        f"✅ <b>Вы выбрали:</b> {role}\n\n"
        f"📋 Опишите, чем вы занимаетесь и какой формат сотрудничества интересует."
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ ЗАЯВКИ ================
@dp.message_handler(Text(equals="📩 Оставить заявку"))
async def handle_request(message: types.Message):
    await message.answer(
        "📋 Опишите вашу задачу одним сообщением.\n"
        "Можно прикрепить фото.",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="🌐 На сайт"))
async def handle_site(message: types.Message):
    await message.answer(
        "🌐 <b>Наш сайт:</b> www.donaqua.pro",
        reply_markup=back_kb,
        parse_mode="HTML"
    )

# ================ ФОТО ================
@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    user = message.from_user
    photo = message.photo[-1]
    
    try:
        await bot.send_photo(
            ADMIN_ID,
            photo.file_id,
            caption=f"📸 <b>ЗАЯВКА С ФОТО</b>\n\n👤 {user.full_name} (@{user.username})\n🆔 {user.id}\n💬 {message.caption or 'Без подписи'}",
            parse_mode="HTML"
        )
        await message.answer("✅ Спасибо! Заявка с фото отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка фото: {e}")
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

# ================ ТЕКСТОВЫЕ ЗАЯВКИ С РАЗДЕЛАМИ ================
user_last_section = {}  # Словарь: user_id -> последний раздел

@dp.message_handler(Text(equals=["🧪 Анализ воды", "💧 Подбор системы очистки", "🏊 Химия и оборудование для бассейнов", "ℹ️ О компании ДОНАКВА", "🤝 Партнёрская программа", "📩 Оставить заявку"]))
async def track_section(message: types.Message):
    """Запоминаем, в каком разделе находится пользователь"""
    section_map = {
        "🧪 Анализ воды": "🧪 АНАЛИЗ ВОДЫ",
        "💧 Подбор системы очистки": "💧 ПОДБОР СИСТЕМЫ",
        "🏊 Химия и оборудование для бассейнов": "🏊 БАССЕЙНЫ",
        "ℹ️ О компании ДОНАКВА": "ℹ️ О КОМПАНИИ",
        "🤝 Партнёрская программа": "🤝 ПАРТНЁРСКАЯ ПРОГРАММА",
        "📩 Оставить заявку": "📩 ЗАЯВКА"
    }
    
    user_last_section[message.from_user.id] = section_map.get(message.text, "📬 ОБЩАЯ ЗАЯВКА")
    await message.answer("📝 Опишите ваш вопрос или задачу", reply_markup=back_kb)

@dp.message_handler()
async def handle_text(message: types.Message):
    # Пропускаем команды и админа
    if message.text.startswith('/') or is_admin(message.from_user.id):
        return
    
    user_id = message.from_user.id
    
    # 1️⃣ Сначала проверяем — есть ли запомненный раздел?
    if user_id in user_last_section:
        section = user_last_section[user_id]
        # Очищаем, чтобы следующее сообщение не ушло в тот же раздел
        del user_last_section[user_id]
    else:
        # 2️⃣ Если нет — пытаемся угадать по тексту
        text_lower = message.text.lower()
        
        if any(word in text_lower for word in ["анализ", "вода", "сдать", "проба", "бутылка", "3500"]):
            section = "🧪 АНАЛИЗ ВОДЫ"
        elif any(word in text_lower for word in ["бассейн", "химия", "хлор", "бром", "альгицид", "фильтр", "насос", "песочный", "картриджный"]):
            section = "🏊 БАССЕЙНЫ"
        elif any(word in text_lower for word in ["систем", "очистк", "фильтр", "умягчение", "обезжелезивание", "осмос", "мембран"]):
            section = "💧 ПОДБОР СИСТЕМЫ"
        elif any(word in text_lower for word in ["партн", "сотрудничеств", "дилер", "монтажник", "сантехник", "прораб", "архитектор", "дизайнер", "бурильщик"]):
            section = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА"
        elif any(word in text_lower for word in ["компани", "донаква", "адрес", "телефон", "сайт", "donaqua"]):
            section = "ℹ️ О КОМПАНИИ"
        else:
            section = "📬 ОБЩАЯ ЗАЯВКА"
    
    user = message.from_user
    
    # Отправляем админу
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
        await message.answer("✅ Спасибо! Ваша заявка отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

# ================ ВЕБ-СЕРВЕР ДЛЯ RENDER ================
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
