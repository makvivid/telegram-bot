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
    waiting_for_confirmation = State()

# ================ ЛОГОТИП ================
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
        print(f"Ошибка логотипа: {e}")
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

# ================ ХРАНИЛИЩЕ РАЗДЕЛОВ ================
user_section = {}

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
        "Мы — профессиональная команда специалистов по очистке воды, "
        "насосному оборудованию и бассейнам.\n\n"
        "🔹 20+ лет опыта\n"
        "🔹 1000+ реализованных проектов\n"
        "🔹 Индивидуальный подход\n\n"
        "📍 ДНР, г. Донецк, ул. Щорса 38\n"
        "📞 +7 949 321‑98‑00\n\n"
        "Выберите нужный раздел 👇"
    )
    
    await send_logo(message.chat.id, welcome_text, main_kb, "HTML")
    
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
newsletter_data = {}

@dp.message_handler(Text(equals="📢 ОТПРАВИТЬ НОВОСТЬ"))
async def start_newsletter(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📝 <b>Отправка новости</b>\n\n"
        "1️⃣ Отправьте текст новости\n"
        "2️⃣ Или отправьте фото с подписью\n"
        "3️⃣ Или просто фото без текста\n\n"
        "❌ Для отмены нажмите кнопку назад",
        parse_mode="HTML",
        reply_markup=back_kb
    )
    await NewsletterStates.waiting_for_text.set()

@dp.message_handler(state=NewsletterStates.waiting_for_text, content_types=['text', 'photo'])
async def get_newsletter_content(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.finish()
        return
    
    if message.text == "🔙 Назад в главное меню":
        await state.finish()
        await cmd_start(message)
        return
    
    if message.photo:
        newsletter_data['photo'] = message.photo[-1].file_id
        newsletter_data['caption'] = message.caption or ""
        preview_text = f"📢 <b>Предпросмотр новости</b>\n\n{message.caption or 'Без подписи'}"
        await message.answer_photo(
            message.photo[-1].file_id,
            caption=preview_text,
            parse_mode="HTML"
        )
    else:
        newsletter_data['text'] = message.text
        newsletter_data.pop('photo', None)
        preview_text = f"📢 <b>Предпросмотр новости</b>\n\n{message.text}"
        await message.answer(preview_text, parse_mode="HTML")
    
    confirm_kb = InlineKeyboardMarkup(row_width=2)
    confirm_kb.add(
        InlineKeyboardButton("✅ Отправить", callback_data="send_news"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_news")
    )
    
    users = load_users()
    await message.answer(
        f"👥 Будет отправлено: <b>{len(users)} пользователям</b>\n\nОтправить?",
        parse_mode="HTML",
        reply_markup=confirm_kb
    )
    await NewsletterStates.waiting_for_confirmation.set()

@dp.callback_query_handler(lambda c: c.data == "send_news", state=NewsletterStates.waiting_for_confirmation)
async def send_newsletter(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    
    if not is_admin(callback_query.from_user.id):
        await state.finish()
        return
    
    users = load_users()
    status_msg = await bot.send_message(
        callback_query.from_user.id,
        f"📤 Отправка {len(users)} пользователям..."
    )
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            if 'photo' in newsletter_data:
                await bot.send_photo(
                    user["id"],
                    newsletter_data['photo'],
                    caption=newsletter_data['caption']
                )
            else:
                await bot.send_message(
                    user["id"],
                    newsletter_data['text']
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
    
    newsletter_data.clear()
    await state.finish()
    await cmd_start(callback_query.message)

@dp.callback_query_handler(lambda c: c.data == "cancel_news", state=NewsletterStates.waiting_for_confirmation)
async def cancel_newsletter(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id, "❌ Рассылка отменена")
    newsletter_data.clear()
    await state.finish()
    await bot.send_message(callback_query.from_user.id, "❌ Рассылка отменена.")
    await cmd_start(callback_query.message)

# ================ РАЗДЕЛ: АНАЛИЗ ВОДЫ ================
@dp.message_handler(Text(equals="🧪 Анализ воды"))
async def handle_analysis(message: types.Message):
    user_section[message.from_user.id] = "🧪 АНАЛИЗ ВОДЫ"
    
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
    user_section[message.from_user.id] = "🧪 АНАЛИЗ ВОДЫ"
    await message.answer(
        "📝 Напишите ваш вопрос по воде или анализу — "
        "я передам его специалисту ДОНАКВА.",
        reply_markup=back_kb
    )

# ================ ПОДБОР СИСТЕМЫ ОЧИСТКИ ================
@dp.message_handler(Text(equals="💧 Подбор системы очистки"))
async def handle_select_system(message: types.Message):
    user_section[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ"
    
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
    user_section[message.from_user.id] = f"💧 ПОДБОР СИСТЕМЫ → {message.text}"
    
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
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ"
    
    text = (
        "🏊 <b>Химия и оборудование для бассейнов</b>\n\n"
        "👇 <b>Выберите раздел:</b>"
    )
    await message.answer(text, reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🧪 Химия для бассейнов"))
async def handle_pool_chemistry(message: types.Message):
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ → Химия"
    
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
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ → Оборудование"
    
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
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ → Комплекты для запуска"
    
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
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ → Индивидуальный подбор"
    
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
    user_section[message.from_user.id] = "ℹ️ О КОМПАНИИ"
    
    text = (
        "🏢 <b>О компании ДОНАКВА</b>\n\n"
        "Высококвалифицированный штат специалистов быстро и качественно осуществит: "
        "подбор, монтаж и сервисное обслуживание оборудования по очистке воды для "
        "квартиры, коттеджа, ресторана или промышленного предприятия.\n\n"
        "🔧 <b>Наши направления:</b>\n"
        "• Промышленные системы подготовки и очистки воды\n"
        "• Коммерческие системы очистки воды\n"
        "• Бытовые системы подготовки и очистки воды\n\n"
        "🧪 <b>Комплексный анализ воды</b>\n"
        "Анализ воды — самый первый и правильный шаг в подборе водоочистного оборудования.\n"
        "Только на основании химического и бактериологического анализов выявляются характер "
        "и степень загрязненности источника воды.\n\n"
        "💎 <b>Наши преимущества:</b>\n"
        "• Индивидуальный подход\n"
        "• Современные технологии\n"
        "• Полный цикл работ: от проекта до сервиса\n"
        "• Оригинальные комплектующие и расходные материалы\n\n"
        "📍 <b>Адрес:</b> г. Донецк, ул. Щорса, д. 38\n"
        "📞 <b>Телефон:</b> +7 949 321‑98‑00\n"
        "🌐 <b>Сайт:</b> www.donaqua.pro"
    )
    
    await send_logo(message.chat.id, text, site_kb, "HTML")

# ================ ПАРТНЁРСКАЯ ПРОГРАММА ================
@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    user_section[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА"
    
    text = (
        "🤝 <b>Партнёрская программа ДОНАКВА</b>\n\n"
        "🎯 <b>Для кого:</b>\n"
        "• Сантехники и монтажники\n"
        "• Архитекторы и дизайнеры\n"
        "• Прорабы и строители\n"
        "• Бурильщики скважин\n"
        "• Управляющие компании\n\n"
        "✅ <b>Что предлагаем:</b>\n"
        "• Выгодные условия\n"
        "• Техническая поддержка\n"
        "• Обучение и консультации\n"
        "• Маркетинговая поддержка\n\n"
        "Выберите вашу сферу:"
    )
    await message.answer(text, reply_markup=partner_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Сантехник / монтажник", "Архитектор / дизайнер", "Прораб / строитель", "Бурильщик скважин", "Другое"]))
async def handle_partner_option(message: types.Message):
    user_section[message.from_user.id] = f"🤝 ПАРТНЁРСКАЯ ПРОГРАММА → {message.text}"
    
    role = message.text
    text = (
        f"✅ <b>Вы выбрали:</b> {role}\n\n"
        f"📋 Опишите, чем вы занимаетесь и какой формат сотрудничества интересует.\n\n"
        f"Мы свяжемся с вами для обсуждения!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ ЗАЯВКИ ================
@dp.message_handler(Text(equals="📩 Оставить заявку"))
async def handle_request(message: types.Message):
    user_section[message.from_user.id] = "📩 ЗАЯВКА"
    
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
    
    if is_admin(user.id):
        return
    
    photo = message.photo[-1]
    section = user_section.get(user.id, "📸 ФОТО")
    
    try:
        await bot.send_photo(
            ADMIN_ID,
            photo.file_id,
            caption=f"🔔 <b>{section}</b>\n\n👤 {user.full_name}\n📱 @{user.username}\n🆔 {user.id}\n💬 {message.caption or 'Без подписи'}",
            parse_mode="HTML"
        )
        await message.answer("✅ Спасибо! Заявка с фото отправлена.", reply_markup=main_kb)
    except:
        await message.answer("✅ Спасибо!", reply_markup=main_kb)
    
    if user.id in user_section:
        del user_section[user.id]

# ================ ТЕКСТОВЫЕ ЗАЯВКИ ================
@dp.message_handler()
async def handle_text(message: types.Message):
    if message.text.startswith('/'):
        return
    
    user = message.from_user
    
    if is_admin(user.id):
        return
    
    section = user_section.get(user.id, "📬 ОБЩАЯ ЗАЯВКА")
    
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
        print(f"Ошибка: {e}")
        await message.answer("✅ Спасибо!", reply_markup=main_kb)
    
    if user.id in user_section:
        del user_section[user.id]

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
    print(f"🖼 Логотип: {LOGO_URL}")
    
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
