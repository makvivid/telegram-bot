import asyncio
import os
import json
import re
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

class ReplyStates(StatesGroup):
    waiting_for_reply = State()

# ================ ЛОГОТИП ================
from aiogram.types import FSInputFile

LOGO_FILE = FSInputFile("logo.png")

async def send_logo(chat_id, caption, reply_markup=None, parse_mode="HTML"):
    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=LOGO_FILE,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except:
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

# ================ ФУНКЦИЯ ДЛЯ КЛИКАБЕЛЬНОГО ИМЕНИ ================
def user_link(user):
    """Возвращает красивую ссылку на пользователя"""
    if user.username:
        return f"@{user.username}"
    else:
        name = user.full_name if user.full_name else "Пользователь"
        return f"[{name}](tg://user?id={user.id})"

# ================ ФУНКЦИЯ ДЛЯ КЛИКАБЕЛЬНОГО ТЕЛЕФОНА (УЛУЧШЕНО) ================
def format_phone(phone):
    """Возвращает кликабельный номер телефона в виде красивой кнопки"""
    # Убираем все пробелы, дефисы, скобки — оставляем только цифры и +
    clean_phone = re.sub(r'[^\d+]', '', phone)
    # Формат для tel: ссылки
    return f'<a href="tel:{clean_phone}">{phone}</a>'

# ================ КЛИКАБЕЛЬНЫЙ ТЕЛЕФОН И АДРЕС ================
PHONE_NUMBER = "+7 949 321‑98‑00"
PHONE_LINK = format_phone(PHONE_NUMBER)
ADDRESS = "г. Донецк, ул. Щорса, д. 38"
ADDRESS_LINK = f'<a href="https://yandex.ru/maps/?text=Донецк+ул.+Щорса+38">{ADDRESS}</a>'

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

# ================ ХРАНИЛИЩЕ ДЛЯ ОТВЕТОВ ================
reply_data = {}

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
        f"📍 {ADDRESS_LINK}\n"
        f"📞 {PHONE_LINK}\n\n"
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
        "Анализ воды — самый первый и правильный шаг в подборе водоочистного оборудования.\n"
        "Только на основании химического и бактериологического анализов выявляются характер "
        "и степень загрязненности источника воды.\n\n"
        "⏱ <b>Срок выполнения:</b> 2–5 рабочих дней\n"
        "💰 <b>Стоимость:</b> 3500 руб.\n\n"
        "📍 <b>Приём проб:</b>\n"
        "📅 Будние дни с 9:00 до 14:00\n"
        f"🏢 ДНР, {ADDRESS_LINK}, магазин ДОНАКВА\n"
        f"📞 {PHONE_LINK}\n\n"
        "📋 <b>Как подготовить пробу:</b>\n"
        "• пластиковая бутылка 1–1,5 л (чистая, без газа)\n"
        "• перед набором слейте воду 2–3 минуты\n"
        "• наберите свежую воду, плотно закройте\n"
        "• храните в холодильнике, доставка в день набора\n\n"
        "✅ После анализа мы подробно объясним результаты\n"
        "и предложим оптимальное решение под ваш бюджет!"
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
        "Мы предлагаем широкий выбор технических решений,\n"
        "основанных на передовых технологиях:\n\n"
        "• Мембранные технологии (обратный осмос)\n"
        "• Оборудование фильтрации и обезжелезивания\n"
        "• Специальные химреагенты\n"
        "• Безреагентные системы\n"
        "• Умягчение и аэрация\n\n"
        "👇 <b>Выберите ваши условия:</b>"
    )
    await message.answer(text, reply_markup=select_system_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Питьевая вода для дома"))
async def handle_drinking_water(message: types.Message):
    user_section[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ → Питьевая вода для дома"

    text = (
        "✅ <b>Вы выбрали:</b> Питьевая вода для дома\n\n"
        "📋 <b>Опишите вашу ситуацию одним сообщением:</b>\n\n"
        "🔹 <b>Источник воды:</b>\n"
        "— скважина / колодец / центральный водопровод\n\n"
        "🔹 <b>Какие проблемы?</b>\n"
        "— запах, вкус, накипь, ржавчина, мутность, песок\n\n"
        "🔹 <b>Сколько человек в семье?</b>\n"
        "— для расчёта суточного потребления\n\n"
        "🔹 <b>Где нужна вода?</b>\n"
        "— только на кухню / во всём доме / для душа\n\n"
        "🔹 <b>Есть ли техника?</b>\n"
        "— бойлер, стиральная машина, кофеварка\n\n"
        "📌 <i>Пример:\n"
        "«Скважина 15 м, вода с запахом сероводорода,\n"
        "семья 4 человека, нужна чистая вода на всю кухню»</i>\n\n"
        "✅ Я передам специалисту — он подберёт систему под ваш бюджет!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Квартира"))
async def handle_apartment(message: types.Message):
    user_section[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ → Квартира"

    text = (
        "✅ <b>Вы выбрали:</b> Квартира\n\n"
        "📋 <b>Опишите вашу ситуацию:</b>\n\n"
        "🔹 <b>Тип дома:</b>\n"
        "— новостройка / старый фонд / вторичка\n\n"
        "🔹 <b>Качество воды:</b>\n"
        "— накипь в чайнике, ржавчина, запах, мутность\n\n"
        "🔹 <b>Где нужна очистка?</b>\n"
        "— только питьевая вода (на кухню) / для всей квартиры\n\n"
        "🔹 <b>Техника:</b>\n"
        "— стиральная машина, бойлер, посудомойка\n\n"
        "🔹 <b>Бюджет:</b>\n"
        "— эконом / стандарт / премиум\n\n"
        "📌 <i>Пример:\n"
        "«Живу на 5 этаже, старая хрущёвка,\n"
        "сильная накипь, нужен компактный фильтр под мойку»</i>\n\n"
        "✅ Я передам ваш запрос — инженер подберёт решение за 1 день!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Частный дом"))
async def handle_house(message: types.Message):
    user_section[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ → Частный дом"

    text = (
        "✅ <b>Вы выбрали:</b> Частный дом\n\n"
        "📋 <b>Опишите вашу ситуацию:</b>\n\n"
        "🔹 <b>Источник воды:</b>\n"
        "— скважина (глубина) / колодец / центральный водопровод\n\n"
        "🔹 <b>Проблемы с водой:</b>\n"
        "— железо, запах, накипь, мутность, жёсткость\n\n"
        "🔹 <b>Количество проживающих:</b>\n"
        "— для расчёта производительности\n\n"
        "🔹 <b>Планируете ли:</b>\n"
        "— полив участка, баню, бассейн\n\n"
        "🔹 <b>Бюджет:</b>\n"
        "— эконом / стандарт / премиум / под ключ\n\n"
        "📌 <i>Пример:\n"
        "«Скважина 25 м, вода ржавая, запах болота,\n"
        "дом 120 м², семья 3 человека, бюджет средний»</i>\n\n"
        "✅ Инженер рассчитает схему и подберёт оборудование!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Офис или бизнес"))
async def handle_office(message: types.Message):
    user_section[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ → Офис или бизнес"

    text = (
        "✅ <b>Вы выбрали:</b> Офис или бизнес\n\n"
        "📋 <b>Опишите вашу ситуацию:</b>\n\n"
        "🔹 <b>Тип объекта:</b>\n"
        "— офис, кафе, ресторан, гостиница, магазин\n\n"
        "🔹 <b>Количество сотрудников/посетителей:</b>\n"
        "— примерная нагрузка\n\n"
        "🔹 <b>Для каких нужд:</b>\n"
        "— питьевая вода (кулер) / приготовление еды / техническая вода\n\n"
        "🔹 <b>Текущие проблемы:</b>\n"
        "— накипь, вкус, запах, налёт на сантехнике\n\n"
        "🔹 <b>Планируемый бюджет:</b>\n"
        "— экспресс / стандарт / премиум\n\n"
        "📌 <i>Пример:\n"
        "«Небольшое кафе, сильная накипь от воды,\n"
        "нужен фильтр под мойку для кофемашины и чая»</i>\n\n"
        "✅ Коммерческий отдел подготовит КП с монтажом и сервисом!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Производство"))
async def handle_industry(message: types.Message):
    user_section[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ → Производство"

    text = (
        "✅ <b>Вы выбрали:</b> Производство\n\n"
        "📋 <b>Опишите вашу ситуацию:</b>\n\n"
        "🔹 <b>Сфера деятельности:</b>\n"
        "— пищевое / техническое / фармацевтика / мойка авто\n\n"
        "🔹 <b>Требуемый объём воды:</b>\n"
        "— м³/час или м³/сутки\n\n"
        "🔹 <b>Необходимое качество:</b>\n"
        "— питьевая / техническая / обессоленная\n\n"
        "🔹 <b>Есть ли готовый проект или КП?</b>\n"
        "— прикрепите файл или опишите требования\n\n"
        "🔹 <b>Сроки запуска:</b>\n"
        "— срочно / 1 месяц / не горит\n\n"
        "📌 <i>Пример:\n"
        "«Автомойка, нужна умягчённая вода,\n"
        "расход 2 м³/час, бюджет до 300 000 руб.»</i>\n\n"
        "✅ Инженеры-технологи свяжутся с вами в ближайшее время!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Просто интересуюсь"))
async def handle_curious(message: types.Message):
    user_section[message.from_user.id] = "💧 ПОДБОР СИСТЕМЫ → Просто интересуюсь"

    text = (
        "✅ <b>Вы выбрали:</b> Просто интересуюсь\n\n"
        "📋 Напишите, что вас интересует:\n\n"
        "🔹 Хотите узнать стоимость оборудования?\n"
        "🔹 Нужна консультация по воде?\n"
        "🔹 Планируете на будущее?\n"
        "🔹 Сравнить технологии?\n\n"
        "📌 <i>Пример:\n"
        "«Думаю о системе для дома, пока собираю информацию.\n"
        "Что лучше — обратный осмос или проточный фильтр?»</i>\n\n"
        "✅ Специалист бесплатно проконсультирует и поможет с выбором!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ БАССЕЙНЫ ================
@dp.message_handler(Text(equals="🏊 Химия и оборудование для бассейнов"))
async def handle_pool(message: types.Message):
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ"

    text = (
        "🏊 <b>Химия и оборудование для бассейнов</b>\n\n"
        "🔹 <b>Химия:</b>\n"
        "— дезинфекция (хлор, бром, активный кислород)\n"
        "— регуляторы pH и щелочности\n"
        "— альгициды (от водорослей)\n"
        "— коагулянты и флокулянты\n"
        "— средства для зимней консервации\n\n"
        "🔹 <b>Оборудование:</b>\n"
        "— фильтры (песочные, картриджные)\n"
        "— насосы и гидромассаж\n"
        "— теплообменники и нагреватели\n"
        "— автоматическая дозация химии\n"
        "— лестницы, поручни, аксессуары\n"
        "— комплекты для запуска бассейна\n\n"
        "👇 <b>Выберите раздел:</b>"
    )
    await message.answer(text, reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🧪 Химия для бассейнов"))
async def handle_pool_chemistry(message: types.Message):
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ → Химия"

    text = (
        "🧪 <b>Химия для бассейнов</b>\n\n"
        "📋 Опишите, какая химия вам нужна:\n\n"
        "🔹 <b>Тип химии:</b>\n"
        "— хлор (быстрый/длинный/таблетки)\n"
        "— бром / активный кислород\n"
        "— альгицид (от водорослей)\n"
        "— pH-минус / pH-плюс\n"
        "— коагулянт / флокулянт\n"
        "— зимняя консервация\n\n"
        "🔹 <b>Объём бассейна:</b>\n"
        "— в м³ или литрах\n\n"
        "🔹 <b>Тип бассейна:</b>\n"
        "— частный / общественный / спа\n"
        "— каркасный / стационарный\n\n"
        "🔹 <b>Проблема:</b>\n"
        "— зелёная вода, мутная, белый налёт, запах\n\n"
        "🔹 <b>Количество:</b>\n"
        "— разовая покупка / регулярная поставка\n\n"
        "📌 <i>Пример:\n"
        "«Нужен хлор в таблетках для бассейна 25 м³,\n"
        "зелёная вода, обрабатываю вручную»</i>\n\n"
        "✅ Мы подберём дозировку и марку — доставим по ДНР!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔧 Оборудование для бассейна"))
async def handle_pool_equipment(message: types.Message):
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ → Оборудование"

    text = (
        "🔧 <b>Оборудование для бассейна</b>\n\n"
        "📋 Опишите, что нужно:\n\n"
        "🔹 <b>Тип оборудования:</b>\n"
        "— фильтр (песочный/картриджный/диатомовый)\n"
        "— насос (циркуляционный/тепловой)\n"
        "— нагреватель / теплообменник\n"
        "— лестница, поручень, светильник\n"
        "— система дозации / автоматика\n\n"
        "🔹 <b>Объём бассейна:</b>\n"
        "— в м³\n\n"
        "🔹 <b>Что случилось?</b>\n"
        "— ремонт, замена, новый монтаж, модернизация\n\n"
        "🔹 <b>Бренд:</b>\n"
        "— есть предпочтения? (Intex, Bestway, Hayward, Emaux)\n\n"
        "🔹 <b>Бюджет:</b>\n"
        "— эконом / стандарт / премиум\n\n"
        "📌 <i>Пример:\n"
        "«Песочный фильтр для бассейна 35 м³,\n"
        "старый сломался, бюджет средний»</i>\n\n"
        "✅ Подберём совместимый аналог или оригинал в наличии!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🚀 Комплекты для запуска"))
async def handle_pool_startup(message: types.Message):
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ → Комплекты для запуска"

    text = (
        "🚀 <b>Комплекты для запуска бассейна</b>\n\n"
        "📋 Опишите ваш бассейн:\n\n"
        "🔹 <b>Объём бассейна:</b>\n"
        "— в м³\n\n"
        "🔹 <b>Тип запуска:</b>\n"
        "— новый бассейн\n"
        "— после зимы\n"
        "— после консервации\n"
        "— после ремонта\n\n"
        "🔹 <b>Тип фильтрации:</b>\n"
        "— песочный / картриджный\n\n"
        "🔹 <b>Источник воды:</b>\n"
        "— водопровод / скважина / привозная\n\n"
        "📌 <i>Пример:\n"
        "«Нужен комплект для запуска бассейна 45 м³,\n"
        "песочный фильтр, вода из скважины»</i>\n\n"
        "✅ Соберём стартовый набор химии + тест-полоски!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🎯 Подбор под мой бассейн"))
async def handle_pool_custom(message: types.Message):
    user_section[message.from_user.id] = "🏊 БАССЕЙНЫ → Индивидуальный подбор"

    text = (
        "🎯 <b>Индивидуальный подбор под ваш бассейн</b>\n\n"
        "📋 Опишите вашу ситуацию максимально подробно:\n\n"
        "🔹 <b>Объём бассейна:</b>\n"
        "— м³\n\n"
        "🔹 <b>Тип бассейна:</b>\n"
        "— частный / общественный\n"
        "— бетонный / каркасный / композитный\n\n"
        "🔹 <b>Задача:</b>\n"
        "— первичный подбор\n"
        "— замена оборудования\n"
        "— модернизация\n"
        "— ремонт\n\n"
        "🔹 <b>Что именно нужно?</b>\n"
        "— химия / оборудование / аксессуары / всё вместе\n\n"
        "🔹 <b>Бюджет:</b>\n"
        "— ориентировочная сумма\n\n"
        "🔹 <b>Сроки:</b>\n"
        "— срочно / в течение месяца / не горит\n\n"
        "📌 <i>Пример:\n"
        "«Бассейн 60 м³, частный, бетонный.\n"
        "Нужен новый насос и автоматическая дозация хлора.\n"
        "Бюджет до 150 000 руб., срочно»</i>\n\n"
        "✅ Подготовим коммерческое предложение в течение 24 часов!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ О КОМПАНИИ ================
@dp.message_handler(Text(equals="ℹ️ О компании ДОНАКВА"))
async def handle_about(message: types.Message):
    user_section[message.from_user.id] = "ℹ️ О КОМПАНИИ"

    text = (
        "🏢 <b>О компании ДОНАКВА</b>\n\n"
        "Высококвалифицированный штат специалистов быстро и качественно осуществит: "
        "подбор, монтаж и сервисное обслуживание оборудования по очистке воды "
        "для квартиры, коттеджа, ресторана или промышленного предприятия.\n\n"
        "🔧 <b>Наши направления:</b>\n"
        "• Промышленные системы подготовки и очистки воды\n"
        "• Коммерческие системы очистки воды\n"
        "• Бытовые системы подготовки и очистки воды\n\n"
        "🧪 <b>Комплексный анализ воды</b>\n"
        "Анализ воды — самый первый и правильный шаг в подборе водоочистного оборудования.\n"
        "Только на основании химического и бактериологического анализов "
        "выявляются характер и степень загрязненности источника воды.\n\n"
        "💎 <b>Наши преимущества:</b>\n"
        "• Индивидуальный подход\n"
        "• Современные технологии\n"
        "• Полный цикл работ: от проекта до сервиса\n"
        "• Оригинальные комплектующие и расходные материалы\n\n"
        f"📍 <b>Адрес:</b> {ADDRESS_LINK}\n"
        f"📞 <b>Телефон:</b> {PHONE_LINK}\n"
        "🌐 <b>Сайт:</b> www.donaqua.pro"
    )

    await send_logo(message.chat.id, text, site_kb, "HTML")

# ================ ПАРТНЁРСКАЯ ПРОГРАММА ================
@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    user_section[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА"

    text = (
        "🤝 <b>Партнёрская программа ДОНАКВА</b>\n\n"
        "Мы открыты к сотрудничеству с профессионалами!\n\n"
        "🎯 <b>Для кого:</b>\n"
        "• Сантехники и монтажники\n"
        "• Архитекторы и дизайнеры\n"
        "• Прорабы и строители\n"
        "• Бурильщики скважин\n"
        "• Управляющие компании\n\n"
        "✅ <b>Что мы предлагаем:</b>\n"
        "• Выгодные условия сотрудничества\n"
        "• Техническая поддержка 24/7\n"
        "• Обучение и консультации\n"
        "• Маркетинговая поддержка\n"
        "• Совместные тендеры и проекты\n\n"
        "👇 <b>Выберите вашу сферу:</b>"
    )
    await message.answer(text, reply_markup=partner_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Сантехник / монтажник"))
async def handle_partner_plumber(message: types.Message):
    user_section[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА → Сантехник / монтажник"

    text = (
        "✅ <b>Вы выбрали:</b> Сантехник / монтажник\n\n"
        "📋 Опишите:\n\n"
        "🔹 Сколько лет работаете?\n"
        "🔹 С каким оборудованием работали?\n"
        "🔹 Какой формат интересен?\n"
        "   — дилер / агент / подрядчик\n"
        "🔹 Есть ли своя бригада?\n"
        "🔹 Нужно ли обучение?\n\n"
        "✅ Мы подготовим индивидуальное предложение!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Архитектор / дизайнер"))
async def handle_partner_architect(message: types.Message):
    user_section[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА → Архитектор / дизайнер"

    text = (
        "✅ <b>Вы выбрали:</b> Архитектор / дизайнер\n\n"
        "📋 Опишите:\n\n"
        "🔹 Работаете с частными или коммерческими проектами?\n"
        "🔹 Нужны ли BIM-модели / чертежи?\n"
        "🔹 Интересует партнёрство на постоянной основе?\n"
        "🔹 Готовы рекомендовать наше оборудование в проектах?\n\n"
        "✅ Предоставим материалы, КП и техподдержку!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Прораб / строитель"))
async def handle_partner_builder(message: types.Message):
    user_section[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА → Прораб / строитель"

    text = (
        "✅ <b>Вы выбрали:</b> Прораб / строитель\n\n"
        "📋 Опишите:\n\n"
        "🔹 Какие объекты ведёте?\n"
        "🔹 Нужен подряд на монтаж систем очистки?\n"
        "🔹 Интересует оптовая закупка оборудования?\n"
        "🔹 Есть ли потребность в шеф-монтаже?\n\n"
        "✅ Рассчитаем смету, предоставим скидку!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Бурильщик скважин"))
async def handle_partner_driller(message: types.Message):
    user_section[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА → Бурильщик скважин"

    text = (
        "✅ <b>Вы выбрали:</b> Бурильщик скважин\n\n"
        "📋 Опишите:\n\n"
        "🔹 Сколько скважин бурите в месяц?\n"
        "🔹 Предлагаете ли клиентам системы очистки?\n"
        "🔹 Нужен ли партнёр по водоподготовке?\n"
        "🔹 Интересует агентское вознаграждение?\n\n"
        "✅ Станем вашим надёжным тылом по воде!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Другое"))
async def handle_partner_other(message: types.Message):
    user_section[message.from_user.id] = "🤝 ПАРТНЁРСКАЯ ПРОГРАММА → Другое"

    text = (
        "✅ <b>Вы выбрали:</b> Другое\n\n"
        "📋 Опишите:\n\n"
        "🔹 Ваша сфера деятельности\n"
        "🔹 Чем можете быть полезны?\n"
        "🔹 Какой формат сотрудничества предлагаете?\n\n"
        "✅ Рассмотрим все предложения!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ ЗАЯВКИ ================
@dp.message_handler(Text(equals="📩 Оставить заявку"))
async def handle_request(message: types.Message):
    user_section[message.from_user.id] = "📩 ЗАЯВКА"

    await message.answer(
        "📋 Опишите вашу задачу одним сообщением.\n\n"
        "Вы можете:\n"
        "• описать проблему с водой\n"
        "• запросить подбор оборудования\n"
        "• узнать стоимость монтажа\n"
        "• прикрепить фото/документы\n\n"
        "✅ Специалист свяжется с вами в ближайшее время!",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="🌐 На сайт"))
async def handle_site(message: types.Message):
    await message.answer(
        "🌐 <b>Наш сайт:</b> www.donaqua.pro",
        reply_markup=back_kb,
        parse_mode="HTML"
    )

# ================ УНИВЕРСАЛЬНЫЙ ОТВЕТ НА ЗАЯВКУ (ЧЕРЕЗ REPLY) ================
@dp.message_handler(lambda msg: is_admin(msg.from_user.id) and msg.reply_to_message is not None)
async def reply_to_user(message: types.Message):
    """Админ отвечает на заявку через reply"""
    reply_text = message.reply_to_message.text or message.reply_to_message.caption
    if not reply_text:
        await message.answer("❌ Не могу определить, кому ответить")
        return

    match = re.search(r'🆔 (\d+)', reply_text)
    if not match:
        await message.answer("❌ Не найден ID пользователя")
        return

    user_id = int(match.group(1))
    admin_reply = message.text

    try:
        await bot.send_message(
            user_id,
            f"📨 <b>Менеджер компании:</b>\n\n{admin_reply}",
            parse_mode="HTML"
        )

        await message.answer(f"✅ Ответ отправлен пользователю ID: {user_id}")

        await bot.send_message(
            ADMIN_ID,
            f"📤 <b>Отправлен ответ</b>\n👤 ID: {user_id}\n💬 {admin_reply}",
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")

# ================ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ДЛЯ ОТПРАВКИ ЛЮБОГО МЕДИА ================
async def forward_media_to_admin(message: types.Message, media_type: str, file_id: str, caption_extra: str = ""):
    """Универсальная функция для пересылки любого типа медиа админу"""
    user = message.from_user
    section = user_section.get(user.id, f"📬 {media_type.upper()}")

    reply_markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user.id}")
    )

    base_caption = f"🔔 <b>{section}</b>\n\n👤 {user_link(user)}\n🆔 {user.id}"
    if caption_extra:
        base_caption += f"\n💬 {caption_extra}"

    try:
        # Определяем метод отправки в зависимости от типа
        if media_type == 'photo':
            await bot.send_photo(ADMIN_ID, file_id, caption=base_caption, parse_mode="Markdown", reply_markup=reply_markup)
        elif media_type == 'video':
            await bot.send_video(ADMIN_ID, file_id, caption=base_caption, parse_mode="Markdown", reply_markup=reply_markup)
        elif media_type == 'voice':
            # Для голосовых caption не поддерживается, отправляем отдельно
            await bot.send_voice(ADMIN_ID, file_id, reply_markup=reply_markup)
            await bot.send_message(ADMIN_ID, base_caption, parse_mode="Markdown")
        elif media_type == 'video_note':
            await bot.send_video_note(ADMIN_ID, file_id, reply_markup=reply_markup)
            await bot.send_message(ADMIN_ID, base_caption, parse_mode="Markdown")
        elif media_type == 'document':
            await bot.send_document(ADMIN_ID, file_id, caption=base_caption, parse_mode="Markdown", reply_markup=reply_markup)
        elif media_type == 'audio':
            await bot.send_audio(ADMIN_ID, file_id, caption=base_caption, parse_mode="Markdown", reply_markup=reply_markup)
        elif media_type == 'location':
            # Для location нужно передавать координаты
            pass # Обрабатывается отдельно
        elif media_type == 'contact':
            pass # Обрабатывается отдельно

        await message.answer(f"✅ Спасибо! {media_type} получено.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка отправки {media_type}: {e}")
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

    if user.id in user_section:
        del user_section[user.id]

# ================ ФОТО ================
@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    if is_admin(message.from_user.id):
        return
    await forward_media_to_admin(message, 'photo', message.photo[-1].file_id, message.caption)

# ================ ВИДЕО ================
@dp.message_handler(content_types=['video'])
async def handle_video(message: types.Message):
    if is_admin(message.from_user.id):
        return
    await forward_media_to_admin(message, 'video', message.video.file_id, message.caption)

# ================ ГОЛОСОВЫЕ ================
@dp.message_handler(content_types=['voice'])
async def handle_voice(message: types.Message):
    if is_admin(message.from_user.id):
        return
    await forward_media_to_admin(message, 'voice', message.voice.file_id)

# ================ ВИДЕОСООБЩЕНИЯ (КРУЖКИ) ================
@dp.message_handler(content_types=['video_note'])
async def handle_video_note(message: types.Message):
    if is_admin(message.from_user.id):
        return
    await forward_media_to_admin(message, 'video_note', message.video_note.file_id)

# ================ ДОКУМЕНТЫ (ФАЙЛЫ) ================
@dp.message_handler(content_types=['document'])
async def handle_document(message: types.Message):
    if is_admin(message.from_user.id):
        return
    file_name = message.document.file_name or ""
    await forward_media_to_admin(message, 'document', message.document.file_id, f"📄 {file_name}\n{message.caption or ''}")

# ================ АУДИО ================
@dp.message_handler(content_types=['audio'])
async def handle_audio(message: types.Message):
    if is_admin(message.from_user.id):
        return
    title = message.audio.title or message.audio.file_name or "Аудиофайл"
    await forward_media_to_admin(message, 'audio', message.audio.file_id, f"🎵 {title}\n{message.caption or ''}")

# ================ ГЕОПОЗИЦИЯ ================
@dp.message_handler(content_types=['location'])
async def handle_location(message: types.Message):
    user = message.from_user
    if is_admin(user.id):
        return

    section = user_section.get(user.id, "📍 ГЕОПОЗИЦИЯ")
    reply_markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user.id}")
    )

    try:
        await bot.send_location(
            ADMIN_ID,
            message.location.latitude,
            message.location.longitude,
            reply_markup=reply_markup
        )
        await bot.send_message(
            ADMIN_ID,
            f"🔔 <b>{section}</b>\n\n👤 {user_link(user)}\n🆔 {user.id}",
            parse_mode="Markdown"
        )
        await message.answer("✅ Спасибо! Геопозиция получена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка геопозиции: {e}")
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

    if user.id in user_section:
        del user_section[user.id]

# ================ КОНТАКТЫ ================
@dp.message_handler(content_types=['contact'])
async def handle_contact(message: types.Message):
    user = message.from_user
    if is_admin(user.id):
        return

    contact = message.contact
    section = user_section.get(user.id, "👤 КОНТАКТ")
    reply_markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user.id}")
    )

    contact_text = f"Имя: {contact.first_name} {contact.last_name or ''}\nТелефон: {contact.phone_number}"
    if contact.user_id:
        contact_text += f"\nID: {contact.user_id}"

    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 <b>{section}</b>\n\n👤 {user_link(user)}\n🆔 {user.id}\n\n📇 {contact_text}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        await message.answer("✅ Спасибо! Контакт получен.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка контакта: {e}")
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
        reply_markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                "💬 Ответить",
                callback_data=f"reply_{user.id}"
            )
        )

        await bot.send_message(
            ADMIN_ID,
            f"🔔 <b>{section}</b>\n\n👤 {user_link(user)}\n🆔 {user.id}\n\n💬 {message.text}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        await message.answer("✅ Спасибо! Ваша заявка отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка: {e}")
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 <b>{section}</b>\n\n👤 {user.full_name} (ID: {user.id})\n💬 {message.text}",
                parse_mode="HTML"
            )
        except:
            pass
        await message.answer("✅ Спасибо!", reply_markup=main_kb)

    if user.id in user_section:
        del user_section[user.id]

# ================ ОБРАБОТЧИК КНОПКИ "ОТВЕТИТЬ" ================
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('reply_'))
async def process_reply_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    if not is_admin(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "⛔ У вас нет прав администратора.")
        return

    user_id = int(callback_query.data.split('_')[1])
    reply_data[callback_query.from_user.id] = user_id

    await bot.send_message(
        callback_query.from_user.id,
        f"✏️ <b>Ответ пользователю ID: {user_id}</b>\n\n"
        f"Напишите ваш ответ в ответном сообщении (Reply) на это сообщение.\n\n"
        f"Или просто отправьте текст ниже.",
        parse_mode="HTML"
    )

    await ReplyStates.waiting_for_reply.set()

@dp.message_handler(state=ReplyStates.waiting_for_reply)
async def handle_reply_text(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.finish()
        return

    user_id = reply_data.get(message.from_user.id)
    if not user_id:
        await message.answer("❌ Сессия ответа истекла. Попробуйте снова.")
        await state.finish()
        return

    reply_text = message.text

    try:
        await bot.send_message(
            user_id,
            f"📨 <b>Менеджер компании:</b>\n\n{reply_text}",
            parse_mode="HTML"
        )

        await message.answer(f"✅ Ответ отправлен пользователю ID: {user_id}")

        await bot.send_message(
            ADMIN_ID,
            f"📤 <b>Отправлен ответ</b>\n👤 ID: {user_id}\n💬 {reply_text}",
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")

    reply_data.pop(message.from_user.id, None)
    await state.finish()

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
    print(f"🖼 Логотип: Загружен из файла logo.png")
    print(f"📞 Телефон: {PHONE_NUMBER} (кликабельный)")
    print(f"📍 Адрес: {ADDRESS} (кликабельный)")

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
