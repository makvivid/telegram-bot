import asyncio
import os
import json
import re
import csv
import logging
from io import StringIO, BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import exceptions
from aiohttp import web
from datetime import datetime, timedelta
import aiohttp

# ================ ЛОГИРОВАНИЕ В ФАЙЛ И КОНСОЛЬ ================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ================ ЦВЕТНЫЕ ЛОГИ ДЛЯ КОНСОЛИ ================
class LogColors:
    OK = '\033[92m'
    WARN = '\033[93m'
    ERROR = '\033[91m'
    INFO = '\033[96m'
    RESET = '\033[0m'

def log_info(msg): 
    print(f"{LogColors.INFO}[INFO]{LogColors.RESET} {msg}")
    logger.info(msg)

def log_ok(msg): 
    print(f"{LogColors.OK}[OK]{LogColors.RESET} {msg}")
    logger.info(msg)

def log_warn(msg): 
    print(f"{LogColors.WARN}[WARN]{LogColors.RESET} {msg}")
    logger.warning(msg)

def log_error(msg): 
    print(f"{LogColors.ERROR}[ERROR]{LogColors.RESET} {msg}")
    logger.error(msg)

# ================ НАСТРОЙКИ ================
API_TOKEN = os.getenv("BOT_TOKEN")

# ================ АДМИНИСТРАТОРЫ ================
ADMIN_IDS = [
    488352806,     # Главный админ (техподдержка)
    1754366929,    # Менеджер
]

# Дополнительные админы из переменной окружения (опционально)
extra_admins = os.getenv("EXTRA_ADMIN_IDS", "")
if extra_admins:
    for admin_id in extra_admins.split(","):
        try:
            ADMIN_IDS.append(int(admin_id.strip()))
        except:
            pass

ADMIN_IDS = list(set(ADMIN_IDS))  # Убираем дубликаты

# ================ РЕЖИМ РАБОТЫ ================
WORKING_HOURS = {
    "start": 9,   # Начало рабочего дня (9:00)
    "end": 15,    # Конец рабочего дня (15:00)
    "days": [0, 1, 2, 3, 4],  # Пн-Пт (0=понедельник, 6=воскресенье)
}

TIMEZONE_OFFSET = 3  # МСК (UTC+3) - Донецк

def get_local_time():
    """Возвращает текущее время с учётом часового пояса"""
    return datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)

def is_working_hours():
    """Проверяет, рабочее ли сейчас время"""
    now = get_local_time()
    current_day = now.weekday()  # 0=Пн, 6=Вс
    current_hour = now.hour
    
    # Проверяем день недели
    if current_day not in WORKING_HOURS["days"]:
        return False
    
    # Проверяем время
    if current_hour < WORKING_HOURS["start"] or current_hour >= WORKING_HOURS["end"]:
        return False
    
    return True

def get_working_hours_message():
    """Возвращает сообщение о режиме работы"""
    return (
        "⏰ <b>Сейчас нерабочее время.</b>\n\n"
        "🕐 Мы работаем:\n"
        "📅 Пн-Пт: 9:00 - 15:00\n"
        "📅 Сб и Вс: выходной\n\n"
        "✅ Ваша заявка сохранена!\n"
        "Мы ответим в рабочее время."
    )

# ================ ПРОВЕРКА ТОКЕНА ================
if not API_TOKEN:
    raise ValueError("ERROR: BOT_TOKEN not set!")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ================ ФАЙЛЫ БАЗЫ ДАННЫХ ================
USERS_FILE = "users.json"
NEWSLETTERS_FILE = "newsletters.json"
REQUESTS_FILE = "requests.json"
ANALYTICS_FILE = "analytics.json"
REVIEWS_FILE = "reviews.json"

# ================ КЭШИРОВАНИЕ ПОЛЬЗОВАТЕЛЕЙ ================
users_cache = None
users_cache_time = None
CACHE_TTL = 60  # Время жизни кэша в секундах

def load_users_cached():
    """Загружает пользователей с кэшированием"""
    global users_cache, users_cache_time
    now = datetime.now()
    
    if users_cache is not None and users_cache_time and (now - users_cache_time).seconds < CACHE_TTL:
        return users_cache
    
    users_cache = load_users()
    users_cache_time = now
    return users_cache

def invalidate_users_cache():
    """Сбрасывает кэш пользователей"""
    global users_cache, users_cache_time
    users_cache = None
    users_cache_time = None

# ================ РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ================
def load_users():
    """Загружает список пользователей из файла"""
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_user(user_id, username, full_name, phone=None, source=None):
    """Сохраняет или обновляет пользователя"""
    users = load_users()
    is_new_user = True
    
    for user in users:
        if user["id"] == user_id:
            is_new_user = False
            if phone:
                user["phone"] = phone
            invalidate_users_cache()
            with open(USERS_FILE, "w") as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            return False
    
    users.append({
        "id": user_id,
        "username": username,
        "full_name": full_name,
        "phone": phone,
        "source": source,
        "joined_date": str(datetime.now())
    })
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    invalidate_users_cache()
    log_ok(f"Новый пользователь сохранён: {user_id} (источник: {source})")
    return True

# ================ РАБОТА С РАССЫЛКАМИ ================
def load_newsletters():
    """Загружает список рассылок"""
    try:
        with open(NEWSLETTERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_newsletter(newsletter_data):
    """Сохраняет рассылку"""
    newsletters = load_newsletters()
    newsletter_data['id'] = str(datetime.now().timestamp())
    newsletter_data['date'] = str(datetime.now())
    newsletters.append(newsletter_data)
    with open(NEWSLETTERS_FILE, "w") as f:
        json.dump(newsletters, f, indent=2, ensure_ascii=False)
    log_ok(f"Рассылка сохранена, ID: {newsletter_data['id']}")
    return newsletter_data['id']

def delete_newsletter(newsletter_id):
    """Удаляет рассылку по ID"""
    newsletters = load_newsletters()
    newsletters = [n for n in newsletters if n.get('id') != newsletter_id]
    with open(NEWSLETTERS_FILE, "w") as f:
        json.dump(newsletters, f, indent=2, ensure_ascii=False)
    log_ok(f"Рассылка удалена, ID: {newsletter_id}")

# ================ РАБОТА С ЗАЯВКАМИ ================
def load_requests():
    """Загружает список заявок"""
    try:
        with open(REQUESTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_request(user_id, request_data, message_id=None, chat_id=None):
    """Сохраняет заявку"""
    requests = load_requests()
    if message_id and chat_id:
        chat_id_str = str(chat_id)
        if chat_id_str.startswith('-100'):
            chat_id_str = chat_id_str[4:]
        request_data['message_link'] = f"https://t.me/c/{chat_id_str}/{message_id}"
    requests[str(user_id)] = request_data
    with open(REQUESTS_FILE, "w") as f:
        json.dump(requests, f, indent=2, ensure_ascii=False)

# ================ РАБОТА С ОТЗЫВАМИ ================
def load_reviews():
    """Загружает список отзывов"""
    try:
        with open(REVIEWS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_review(user_id, username, full_name, rating, text):
    """Сохраняет отзыв"""
    reviews = load_reviews()
    reviews.append({
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "rating": rating,
        "text": text,
        "date": str(datetime.now())
    })
    with open(REVIEWS_FILE, "w") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    log_ok(f"Отзыв сохранён от пользователя {user_id}")

# ================ АНАЛИТИКА ИСТОЧНИКОВ ================
def load_analytics():
    """Загружает аналитику"""
    try:
        with open(ANALYTICS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"sources": {}, "total": 0}

def save_analytics(source):
    """Сохраняет источник перехода"""
    analytics = load_analytics()
    analytics['total'] = analytics.get('total', 0) + 1
    analytics['sources'] = analytics.get('sources', {})
    analytics['sources'][source] = analytics['sources'].get(source, 0) + 1
    analytics['last_update'] = str(datetime.now())
    
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    log_info(f"Аналитика: источник '{source}' зафиксирован")

# ================ АВТООЧИСТКА СТАРЫХ ЗАЯВОК ================
def cleanup_old_requests(days=30):
    """Удаляет заявки старше N дней"""
    requests = load_requests()
    now = datetime.now()
    new_requests = {}
    
    for user_id, data in requests.items():
        try:
            req_time = datetime.fromisoformat(data['time'])
            if (now - req_time).days < days:
                new_requests[user_id] = data
        except:
            pass
    
    with open(REQUESTS_FILE, "w") as f:
        json.dump(new_requests, f, indent=2, ensure_ascii=False)
    
    deleted_count = len(requests) - len(new_requests)
    if deleted_count > 0:
        log_info(f"Очистка: удалено {deleted_count} старых заявок")

# ================ АНТИСПАМ ================
last_message_time = {}

def check_spam(user_id):
    """Проверяет, не спамит ли пользователь"""
    if is_admin(user_id):
        return True
    now = datetime.now()
    if user_id in last_message_time:
        if now - last_message_time[user_id] < timedelta(seconds=2):
            return False
    last_message_time[user_id] = now
    return True

# ================ РЕЙТ-ЛИМИТ ДЛЯ РАССЫЛОК ================
last_newsletter_time = None

# ================ СОСТОЯНИЯ FSM ================
class NewsletterStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirmation = State()

class ReplyStates(StatesGroup):
    waiting_for_reply = State()

class RequestStates(StatesGroup):
    waiting_for_phone = State()

class ReviewStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_text = State()

# ================ ЛОГОТИП ================
LOGO_PATH = "logo.png"

async def send_logo(chat_id, caption, reply_markup=None, parse_mode="HTML"):
    """Отправляет логотип с текстом или просто текст, если логотипа нет"""
    try:
        if os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, 'rb') as photo:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=InputFile(photo),
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        return True
    except Exception as e:
        log_error(f"Ошибка логотипа: {e}")
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

# ================ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ================
def user_link(user):
    """Возвращает кликабельную ссылку на пользователя"""
    if user.username:
        return f"@{user.username}"
    else:
        name = user.full_name if user.full_name else "Пользователь"
        return f"[{name}](tg://user?id={user.id})"

def format_phone(phone):
    """Форматирует телефон как кликабельную ссылку"""
    clean_phone = re.sub(r'[^\d+]', '', phone)
    return f'<a href="tel:{clean_phone}">{phone}</a>'

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

# ================ ФОРМАТИРОВАНИЕ ЗАЯВКИ ================
def format_request(user, section, message_text, phone=None, status="NEW", source=None):
    """Форматирует заявку для отправки админам"""
    name = user.full_name if user.full_name else "Не указано"
    username = f"@{user.username}" if user.username else "отсутствует"
    phone_display = phone if phone else "не указан"
    now = get_local_time().strftime("%d.%m.%Y %H:%M")
    
    status_emoji = {"NEW": "🟡", "WORK": "🟠", "DONE": "🟢"}.get(status, "⚪")
    
    section_emoji = {
        "🧪 АНАЛИЗ ВОДЫ": "🧪",
        "💧 ПОДБОР СИСТЕМЫ": "💧",
        "🏊 БАССЕЙНЫ": "🏊",
        "ℹ️ О КОМПАНИИ": "ℹ️",
        "🤝 ПАРТНЁРСКАЯ ПРОГРАММА": "🤝",
        "📩 ЗАЯВКА": "📩",
        "📸 ФОТО": "📸",
        "🎤 ГОЛОСОВОЕ": "🎤",
        "🎥 ВИДЕО": "🎥",
        "📎 ДОКУМЕНТ": "📎",
        "📬 ОБЩАЯ ЗАЯВКА": "📬",
        "⭐ ОТЗЫВ": "⭐",
    }.get(section, "📌")
    
    source_emoji = {
        "website": "🌐 Сайт",
        "instagram": "📸 Instagram",
        "facebook": "📘 Facebook",
        "vk": "💙 VK",
        "shop": "🏪 Магазин",
        "card": "💳 Визитка",
        "ads": "📢 Реклама",
        "telegram": "✈️ Telegram"
    }.get(source, "")
    
    source_line = f"\n<b>📍 Источник:</b> {source_emoji}" if source_emoji else ""
    
    # Статус рабочего времени
    working_status = "🟢 Рабочее время" if is_working_hours() else "🔴 Нерабочее время"
    
    text = (
        f"<b>{status_emoji} НОВАЯ ЗАЯВКА</b>\n\n"
        f"<b>👤 Имя:</b> {name}\n"
        f"<b>🔗 Username:</b> {username}\n"
        f"<b>🆔 ID:</b> <code>{user.id}</code>\n\n"
        f"<b>📱 Телефон:</b> {phone_display}\n"
        f"<b>📍 Раздел:</b> {section_emoji} {section}"
        f"{source_line}\n\n"
        f"<b>💬 Сообщение:</b>\n{message_text}\n\n"
        f"<b>🕒 Дата:</b> {now}\n"
        f"<b>⏰ Статус времени:</b> {working_status}\n"
        f"<b>📊 Статус заявки:</b> {status_emoji} {status}"
    )
    return text

# ================ КОНТАКТНЫЕ ДАННЫЕ ================
PHONE_NUMBER = "+7 949 321‑98‑00"
PHONE_LINK = format_phone(PHONE_NUMBER)
ADDRESS = "г. Донецк, ул. Щорса, д. 38"
ADDRESS_LINK = f'<a href="https://yandex.ru/maps/?text=Донецк+ул.+Щорса+38">{ADDRESS}</a>'

# ================ КЛАВИАТУРЫ ================
phone_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
phone_kb.add(KeyboardButton("📱 Отправить номер", request_contact=True))

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧪 Анализ воды"), KeyboardButton(text="💧 Подбор системы очистки")],
        [KeyboardButton(text="🏊 Химия и оборудование для бассейнов")],
        [KeyboardButton(text="ℹ️ О компании ДОНАКВА")],
        [KeyboardButton(text="🤝 Партнёрская программа")],
        [KeyboardButton(text="📩 Оставить заявку"), KeyboardButton(text="⭐ Оставить отзыв")],
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
    """Возвращает клавиатуру для администратора"""
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("📢 Новая рассылка"),
        KeyboardButton("📋 Мои рассылки"),
        KeyboardButton("👥 Статистика"),
        KeyboardButton("💬 Быстрые ответы"),
        KeyboardButton("📤 Экспорт базы"),
        KeyboardButton("⭐ Отзывы"),
        KeyboardButton("👨‍💼 Админы")
    )
    return kb

# ================ ОТПРАВКА ВСЕМ АДМИНАМ ================
async def notify_all_admins(text, reply_markup=None, parse_mode="HTML"):
    """Отправляет сообщение всем администраторам"""
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        except Exception as e:
            log_error(f"Ошибка отправки админу {admin_id}: {e}")

async def send_media_to_all_admins(media_type, file_id, caption, reply_markup=None):
    """Отправляет медиафайл всем администраторам"""
    for admin_id in ADMIN_IDS:
        try:
            if media_type == "photo":
                await bot.send_photo(admin_id, file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
            elif media_type == "video":
                await bot.send_video(admin_id, file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
            elif media_type == "voice":
                await bot.send_voice(admin_id, file_id, reply_markup=reply_markup)
                await bot.send_message(admin_id, caption, parse_mode="HTML")
            elif media_type == "document":
                await bot.send_document(admin_id, file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
        except Exception as e:
            log_error(f"Ошибка отправки медиа админу {admin_id}: {e}")

# ================ ХРАНИЛИЩА ================
user_section = {}      # Текущий раздел пользователя
user_source = {}       # Источник перехода пользователя
reply_data = {}        # Данные для ответа
review_data = {}       # Данные для отзыва

# ================ УВЕДОМЛЕНИЕ О НОВОМ ПОЛЬЗОВАТЕЛЕ ================
async def notify_new_user(user_id, username, full_name, source=None):
    """Уведомляет всех админов о новом пользователе"""
    try:
        if username:
            username_link = f"@{username}"
        else:
            username_link = f'<a href="tg://user?id={user_id}">{full_name}</a>'
        
        source_text = ""
        if source:
            source_names = {
                "website": "🌐 Сайт",
                "instagram": "📸 Instagram",
                "facebook": "📘 Facebook",
                "vk": "💙 VK",
                "shop": "🏪 Магазин",
                "card": "💳 Визитка",
                "ads": "📢 Реклама",
                "telegram": "✈️ Telegram"
            }
            source_text = f"\n📍 Источник: {source_names.get(source, source)}"
        
        await notify_all_admins(
            f"🆕 <b>Новый пользователь!</b>\n\n"
            f"👤 {username_link}\n"
            f"🆔 ID: <code>{user_id}</code>"
            f"{source_text}\n"
            f"🕐 {get_local_time().strftime('%d.%m.%Y %H:%M')}"
        )
    except Exception as e:
        log_error(f"Ошибка уведомления о новом пользователе: {e}")

# ================ АВТООТВЕТ С УЧЁТОМ РАБОЧЕГО ВРЕМЕНИ ================
def get_auto_reply_text(is_first_time=True):
    """Возвращает текст автоответа с учётом рабочего времени"""
    if is_working_hours():
        if is_first_time:
            return (
                "✅ <b>Спасибо за обращение!</b>\n\n"
                "Ваша заявка получена и передана специалисту.\n"
                "Мы свяжемся с вами в ближайшее время!\n\n"
                f"📞 Телефон: {PHONE_NUMBER}\n"
                f"📍 Адрес: {ADDRESS}\n"
                "🏪 Самовывоз из магазина\n"
                "🌐 Сайт: www.donaqua.pro"
            )
        else:
            return "✅ Спасибо! Ваша заявка получена."
    else:
        return (
            "✅ <b>Спасибо за обращение!</b>\n\n"
            f"{get_working_hours_message()}\n\n"
            f"📞 Телефон: {PHONE_NUMBER}\n"
            f"📍 Адрес: {ADDRESS}\n"
            "🏪 Самовывоз из магазина\n"
            "🌐 Сайт: www.donaqua.pro"
        )

# ================================================================================
# ОБРАБОТЧИКИ КОМАНД
# ================================================================================

# ================ СТАРТ ================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    if not check_spam(message.from_user.id):
        return
    
    # Получаем параметры после /start (UTM-метки)
    args = message.get_args()
    source = None
    
    if args:
        source = args
        save_analytics(source)
        user_source[message.from_user.id] = source
    
    # Проверяем, новый ли пользователь
    is_new = save_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        source=source
    )
    
    # Если новый — уведомляем всех админов
    if is_new:
        asyncio.create_task(notify_new_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            source
        ))

    # Формируем приветствие в зависимости от источника
    if source == 'website':
        welcome_text = (
            "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
            "Рады, что вы перешли с нашего сайта!\n\n"
            "🔹 20+ лет опыта\n"
            "🔹 1000+ реализованных проектов\n"
            "🔹 Индивидуальный подход\n\n"
            f"📍 {ADDRESS_LINK}\n"
            f"📞 {PHONE_LINK}\n"
            "🏪 Самовывоз из магазина\n\n"
            "Чем можем помочь? Выберите раздел 👇"
        )
    elif source == 'instagram':
        welcome_text = (
            "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
            "Рады видеть подписчика из Instagram! 📸\n\n"
            "🔹 20+ лет опыта\n"
            "🔹 1000+ реализованных проектов\n"
            "🔹 Индивидуальный подход\n\n"
            f"📍 {ADDRESS_LINK}\n"
            f"📞 {PHONE_LINK}\n"
            "🏪 Самовывоз из магазина\n\n"
            "Выберите нужный раздел 👇"
        )
    elif source == 'shop':
        welcome_text = (
            "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
            "Спасибо, что отсканировали QR-код в нашем магазине! 🏪\n\n"
            "🔹 20+ лет опыта\n"
            "🔹 1000+ реализованных проектов\n"
            "🔹 Индивидуальный подход\n\n"
            f"📍 {ADDRESS_LINK}\n"
            f"📞 {PHONE_LINK}\n\n"
            "Здесь вы можете получить консультацию или оставить заявку 👇"
        )
    elif source in ['vk', 'facebook']:
        welcome_text = (
            "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
            "Рады видеть вас из социальных сетей! 💙\n\n"
            "🔹 20+ лет опыта\n"
            "🔹 1000+ реализованных проектов\n"
            "🔹 Индивидуальный подход\n\n"
            f"📍 {ADDRESS_LINK}\n"
            f"📞 {PHONE_LINK}\n"
            "🏪 Самовывоз из магазина\n\n"
            "Выберите нужный раздел 👇"
        )
    elif source == 'ads':
        welcome_text = (
            "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
            "Мы — профессиональная команда специалистов по очистке воды, "
            "насосному оборудованию и бассейнам.\n\n"
            "🔹 20+ лет опыта\n"
            "🔹 1000+ реализованных проектов\n"
            "🔹 Индивидуальный подход\n\n"
            f"📍 {ADDRESS_LINK}\n"
            f"📞 {PHONE_LINK}\n"
            "🏪 Самовывоз из магазина\n\n"
            "Выберите нужный раздел 👇"
        )
    else:
        welcome_text = (
            "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
            "Мы — профессиональная команда специалистов по очистке воды, "
            "насосному оборудованию и бассейнам.\n\n"
            "🔹 20+ лет опыта\n"
            "🔹 1000+ реализованных проектов\n"
            "🔹 Индивидуальный подход\n\n"
            f"📍 {ADDRESS_LINK}\n"
            f"📞 {PHONE_LINK}\n"
            "🏪 Самовывоз из магазина\n\n"
            "Выберите нужный раздел 👇"
        )

    # Показываем разные клавиатуры для админов и обычных пользователей
    if is_admin(message.from_user.id):
        await send_logo(message.chat.id, welcome_text, get_admin_kb(), "HTML")
        await message.answer("👑 ПАНЕЛЬ АДМИНИСТРАТОРА", reply_markup=get_admin_kb())
    else:
        await send_logo(message.chat.id, welcome_text, main_kb, "HTML")

# ================ НАЗАД В ГЛАВНОЕ МЕНЮ ================
@dp.message_handler(Text(equals="🔙 Назад в главное меню"))
async def back_to_main(message: types.Message):
    """Возврат в главное меню"""
    await cmd_start(message)

# ================================================================================
# АДМИН-ПАНЕЛЬ
# ================================================================================

# ================ УПРАВЛЕНИЕ АДМИНАМИ ================
@dp.message_handler(Text(equals="👨‍💼 Админы"))
async def show_admins(message: types.Message):
    """Показывает список администраторов"""
    if not is_admin(message.from_user.id):
        return
    
    admins_text = "👨‍💼 <b>Список администраторов:</b>\n\n"
    
    admin_roles = {
        488352806: "Главный админ (техподдержка)",
        1754366929: "Менеджер"
    }
    
    for i, admin_id in enumerate(ADMIN_IDS, 1):
        try:
            admin_info = await bot.get_chat(admin_id)
            name = admin_info.full_name or "Без имени"
            username = f"@{admin_info.username}" if admin_info.username else "нет username"
            role = admin_roles.get(admin_id, "Администратор")
            admins_text += f"{i}. <b>{name}</b> ({username})\n   🔹 {role}\n   🆔 <code>{admin_id}</code>\n\n"
        except:
            role = admin_roles.get(admin_id, "Администратор")
            admins_text += f"{i}. 🔹 {role}\n   🆔 <code>{admin_id}</code> (не удалось получить информацию)\n\n"
    
    admins_text += (
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📝 <b>Как добавить нового админа:</b>\n"
        "1. Добавьте ID в переменную ADMIN_IDS в коде\n"
        "2. Или в переменную окружения EXTRA_ADMIN_IDS\n\n"
        "Пример: EXTRA_ADMIN_IDS=123456789,987654321"
    )
    
    await message.answer(admins_text, parse_mode="HTML", reply_markup=get_admin_kb())

# ================ СТАТИСТИКА ================
@dp.message_handler(Text(equals="👥 Статистика"))
async def show_stats(message: types.Message):
    """Показывает статистику бота"""
    if not is_admin(message.from_user.id):
        return

    users = load_users_cached()
    newsletters = load_newsletters()
    analytics = load_analytics()
    reviews = load_reviews()
    
    now = datetime.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    new_today = 0
    new_week = 0
    new_month = 0
    
    for user in users:
        try:
            joined = datetime.fromisoformat(user['joined_date'])
            if joined.date() == today:
                new_today += 1
            if joined > week_ago:
                new_week += 1
            if joined > month_ago:
                new_month += 1
        except:
            pass

    # Аналитика источников
    sources_text = ""
    sources = analytics.get('sources', {})
    if sources:
        sources_text = "\n📊 <b>Источники переходов:</b>\n"
        source_names = {
            'website': '🌐 Сайт',
            'instagram': '📸 Instagram',
            'facebook': '📘 Facebook',
            'vk': '💙 VK',
            'shop': '🏪 Магазин',
            'card': '💳 Визитка',
            'ads': '📢 Реклама',
            'telegram': '✈️ Telegram'
        }
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            name = source_names.get(source, f"📌 {source}")
            sources_text += f"• {name}: <b>{count}</b>\n"

    # Средний рейтинг отзывов
    avg_rating = 0
    if reviews:
        total_rating = sum(r.get('rating', 0) for r in reviews)
        avg_rating = round(total_rating / len(reviews), 1)

    # Статус рабочего времени
    working_status = "🟢 Рабочее время" if is_working_hours() else "🔴 Нерабочее время"

    text = (
        f"📊 <b>Статистика бота ДОНАКВА</b>\n\n"
        f"⏰ <b>Текущий статус:</b> {working_status}\n"
        f"🕐 Время: {get_local_time().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Всего пользователей: <b>{len(users)}</b>\n"
        f"🆕 Новых за сегодня: <b>{new_today}</b>\n"
        f"📅 Новых за неделю: <b>{new_week}</b>\n"
        f"📆 Новых за месяц: <b>{new_month}</b>\n\n"
        f"📨 Всего рассылок: <b>{len(newsletters)}</b>\n"
        f"⭐ Отзывов: <b>{len(reviews)}</b> (средний рейтинг: {avg_rating}⭐)\n"
        f"👨‍💼 Админов: <b>{len(ADMIN_IDS)}</b>\n"
        f"{sources_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Последние 5 пользователей:</b>\n"
    )
    
    for user in users[-5:][::-1]:
        name = user['full_name'][:20] if user.get('full_name') else "Без имени"
        user_id = user['id']
        username = user.get('username', '')
        user_source_data = user.get('source', '')
        
        if username:
            user_ref = f"@{username}"
        else:
            user_ref = f'<a href="tg://user?id={user_id}">{name}</a>'
        
        joined = user.get('joined_date', '')[:10]
        source_icon = ""
        if user_source_data:
            source_icons = {
                'website': '🌐',
                'instagram': '📸',
                'facebook': '📘',
                'vk': '💙',
                'shop': '🏪',
                'card': '💳',
                'ads': '📢'
            }
            source_icon = source_icons.get(user_source_data, '📌') + " "
        
        text += f"• {source_icon}{user_ref} — {joined}\n"
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_kb())

# ================ ОТЗЫВЫ (КНОПКА ДЛЯ ПОЛЬЗОВАТЕЛЯ) ================
@dp.message_handler(Text(equals="⭐ Оставить отзыв"))
async def start_review(message: types.Message):
    """Начинает процесс сбора отзыва от пользователя"""
    if is_admin(message.from_user.id):
        # Для админа — показываем статистику отзывов
        await show_reviews(message)
        return
    
    user_section[message.from_user.id] = "⭐ ОТЗЫВ"
    
    kb = InlineKeyboardMarkup(row_width=5)
    kb.add(
        InlineKeyboardButton("1⭐", callback_data="rating_1"),
        InlineKeyboardButton("2⭐", callback_data="rating_2"),
        InlineKeyboardButton("3⭐", callback_data="rating_3"),
        InlineKeyboardButton("4⭐", callback_data="rating_4"),
        InlineKeyboardButton("5⭐", callback_data="rating_5"),
    )
    
    await message.answer(
        "⭐ <b>Оставьте отзыв о ДОНАКВА</b>\n\n"
        "Нам важно ваше мнение! Оцените нашу работу от 1 до 5 звёзд:",
        parse_mode="HTML",
        reply_markup=kb
    )
    await ReviewStates.waiting_for_rating.set()

@dp.callback_query_handler(lambda c: c.data.startswith('rating_'), state=ReviewStates.waiting_for_rating)
async def process_rating(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор рейтинга"""
    rating = int(callback.data.split('_')[1])
    review_data[callback.from_user.id] = {"rating": rating}
    
    await callback.answer(f"Вы выбрали {rating}⭐")
    
    skip_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⏭ Пропустить", callback_data="skip_review_text")
    )
    
    await callback.message.edit_text(
        f"⭐ <b>Вы поставили: {'⭐' * rating}</b>\n\n"
        "Напишите ваш отзыв (что понравилось, что можно улучшить):\n\n"
        "<i>Или нажмите «Пропустить», если не хотите оставлять комментарий</i>",
        parse_mode="HTML",
        reply_markup=skip_kb
    )
    await ReviewStates.waiting_for_text.set()

@dp.callback_query_handler(lambda c: c.data == "skip_review_text", state=ReviewStates.waiting_for_text)
async def skip_review_text(callback: types.CallbackQuery, state: FSMContext):
    """Пропуск текста отзыва"""
    user = callback.from_user
    rating = review_data.get(user.id, {}).get("rating", 5)
    
    save_review(user.id, user.username, user.full_name, rating, "")
    
    # Уведомляем всех админов
    await notify_all_admins(
        f"⭐ <b>Новый отзыв!</b>\n\n"
        f"👤 {user.full_name}\n"
        f"🔗 @{user.username if user.username else 'нет username'}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"⭐ Оценка: {'⭐' * rating}\n"
        f"💬 Комментарий: <i>без комментария</i>"
    )
    
    await callback.message.edit_text(
        "✅ <b>Спасибо за вашу оценку!</b>\n\n"
        "Мы ценим каждый отзыв и стараемся становиться лучше! 💙",
        parse_mode="HTML"
    )
    
    review_data.pop(user.id, None)
    await state.finish()

@dp.message_handler(state=ReviewStates.waiting_for_text)
async def process_review_text(message: types.Message, state: FSMContext):
    """Обрабатывает текст отзыва"""
    user = message.from_user
    rating = review_data.get(user.id, {}).get("rating", 5)
    review_text = message.text
    
    save_review(user.id, user.username, user.full_name, rating, review_text)
    
    # Уведомляем всех админов
    await notify_all_admins(
        f"⭐ <b>Новый отзыв!</b>\n\n"
        f"👤 {user.full_name}\n"
        f"🔗 @{user.username if user.username else 'нет username'}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"⭐ Оценка: {'⭐' * rating}\n"
        f"💬 Комментарий:\n{review_text}"
    )
    
    await message.answer(
        "✅ <b>Спасибо за ваш отзыв!</b>\n\n"
        "Мы ценим каждый отзыв и стараемся становиться лучше! 💙",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    
    review_data.pop(user.id, None)
    await state.finish()

# ================ ПРОСМОТР ОТЗЫВОВ (АДМИН) ================
@dp.message_handler(Text(equals="⭐ Отзывы"))
async def show_reviews(message: types.Message):
    """Показывает отзывы для админа"""
    if not is_admin(message.from_user.id):
        return
    
    reviews = load_reviews()
    
    if not reviews:
        await message.answer("📭 Отзывов пока нет", reply_markup=get_admin_kb())
        return
    
    # Статистика отзывов
    total = len(reviews)
    avg_rating = round(sum(r.get('rating', 0) for r in reviews) / total, 1)
    
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        rating = r.get('rating', 0)
        if rating in rating_counts:
            rating_counts[rating] += 1
    
    stats_text = (
        f"⭐ <b>Статистика отзывов</b>\n\n"
        f"📊 Всего: <b>{total}</b>\n"
        f"⭐ Средний рейтинг: <b>{avg_rating}</b>\n\n"
        f"5⭐ — {rating_counts[5]} отзывов\n"
        f"4⭐ — {rating_counts[4]} отзывов\n"
        f"3⭐ — {rating_counts[3]} отзывов\n"
        f"2⭐ — {rating_counts[2]} отзывов\n"
        f"1⭐ — {rating_counts[1]} отзывов\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>Последние 5 отзывов:</b>\n"
    )
    
    await message.answer(stats_text, parse_mode="HTML")
    
    # Показываем последние 5 отзывов
    for review in reviews[-5:][::-1]:
        rating = review.get('rating', 0)
        text = review.get('text', 'без комментария')
        date = review.get('date', '')[:16]
        name = review.get('full_name', 'Аноним')
        username = review.get('username', '')
        
        user_info = f"@{username}" if username else name
        
        review_text = (
            f"{'⭐' * rating}\n"
            f"👤 {user_info}\n"
            f"💬 {text if text else '<i>без комментария</i>'}\n"
            f"📅 {date}"
        )
        
        await message.answer(review_text, parse_mode="HTML")
    
    # Кнопка экспорта отзывов
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("📤 Экспорт отзывов", callback_data="export_reviews")
    )
    await message.answer("📤 Хотите экспортировать все отзывы?", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "export_reviews")
async def export_reviews(callback: types.CallbackQuery):
    """Экспортирует отзывы в CSV"""
    if not is_admin(callback.from_user.id):
        return
    
    reviews = load_reviews()
    
    output = StringIO()
    fieldnames = ['date', 'full_name', 'username', 'user_id', 'rating', 'text']
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for review in reviews:
        writer.writerow({
            'date': review.get('date', ''),
            'full_name': review.get('full_name', ''),
            'username': review.get('username', ''),
            'user_id': review.get('user_id', ''),
            'rating': review.get('rating', ''),
            'text': review.get('text', '')
        })
    
    file_content = output.getvalue().encode('utf-8-sig')
    
    await bot.send_document(
        callback.from_user.id,
        document=InputFile(BytesIO(file_content), filename=f"donaqua_reviews_{datetime.now().strftime('%Y%m%d')}.csv"),
        caption=f"⭐ <b>Экспорт отзывов</b>\nВсего: {len(reviews)}",
        parse_mode="HTML"
    )
    await callback.answer("✅ Отзывы экспортированы")

# ================ БЫСТРЫЕ ОТВЕТЫ ================
@dp.message_handler(Text(equals="💬 Быстрые ответы"))
async def quick_replies(message: types.Message):
    """Показывает быстрые шаблоны ответов для админа"""
    if not is_admin(message.from_user.id):
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("✅ Заявка принята", callback_data="quick_1"),
        InlineKeyboardButton("📋 Нужен анализ воды", callback_data="quick_2"),
        InlineKeyboardButton("💰 Отправлю КП", callback_data="quick_3"),
        InlineKeyboardButton("📞 Позвоните нам", callback_data="quick_4"),
        InlineKeyboardButton("🌐 Информация на сайте", callback_data="quick_5"),
        InlineKeyboardButton("❓ Уточните детали", callback_data="quick_6"),
        InlineKeyboardButton("🏪 Самовывоз из магазина", callback_data="quick_7")
    )
    
    await message.answer(
        "💬 <b>Быстрые ответы:</b>\n\n"
        "Выберите шаблон, скопируйте и ответьте (Reply) на сообщение клиента:",
        parse_mode="HTML",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data.startswith('quick_'))
async def process_quick_reply(callback: types.CallbackQuery):
    """Обрабатывает выбор быстрого ответа"""
    templates = {
        'quick_1': '✅ Ваша заявка принята! Наш менеджер свяжется с вами.',
        'quick_2': '🧪 Для точного подбора системы рекомендуем сделать анализ воды. Стоимость 3500 руб., срок 2-5 дней. Приём проб: Пн-Пт 9:00-14:00.',
        'quick_3': '📋 Подготовлю для вас коммерческое предложение. Уточните, пожалуйста, ваш бюджет?',
        'quick_4': f'📞 Позвоните нам: {PHONE_NUMBER}. Или оставьте номер — мы перезвоним!',
        'quick_5': '🌐 Вся информация на нашем сайте: www.donaqua.pro',
        'quick_6': '❓ Уточните, пожалуйста, детали: что именно вас интересует?',
        'quick_7': f'🏪 Товар можно забрать самовывозом из нашего магазина по адресу: {ADDRESS}. Режим работы: Пн-Пт 9:00-15:00.'
    }
    
    text = templates.get(callback.data, '')
    await callback.answer("Скопируйте текст ниже")
    await bot.send_message(
        callback.from_user.id, 
        f"📋 <b>Шаблон для копирования:</b>\n\n<code>{text}</code>\n\n"
        f"👆 Нажмите на текст, чтобы скопировать",
        parse_mode="HTML"
    )

# ================ ЭКСПОРТ БАЗЫ ================
@dp.message_handler(Text(equals="📤 Экспорт базы"))
async def export_data(message: types.Message):
    """Экспортирует базу пользователей в CSV"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        users = load_users()
        
        output = StringIO()
        fieldnames = ['id', 'username', 'full_name', 'phone', 'source', 'joined_date']
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for user in users:
            writer.writerow({
                'id': user.get('id', ''),
                'username': user.get('username', ''),
                'full_name': user.get('full_name', ''),
                'phone': user.get('phone', ''),
                'source': user.get('source', ''),
                'joined_date': user.get('joined_date', '')
            })
        
        file_content = output.getvalue().encode('utf-8-sig')
        
        await bot.send_document(
            message.chat.id,
            document=InputFile(BytesIO(file_content), filename=f"donaqua_users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"),
            caption=f"📊 <b>База пользователей ДОНАКВА</b>\n\n"
                   f"👥 Всего: <b>{len(users)}</b>\n"
                   f"📅 Дата: {get_local_time().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML"
        )
        log_ok(f"Экспорт базы выполнен: {len(users)} пользователей")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка экспорта: {e}")
        log_error(f"Ошибка экспорта: {e}")

# ================ РАССЫЛКА ================
newsletter_data = {}

@dp.message_handler(Text(equals="📢 Новая рассылка"))
async def start_newsletter(message: types.Message):
    """Начинает создание новой рассылки"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📝 <b>Новая рассылка</b>\n\n"
        "1️⃣ Отправьте текст\n"
        "2️⃣ Или фото с подписью\n"
        "3️⃣ Или просто фото\n\n"
        "❌ Отмена — кнопка назад",
        parse_mode="HTML",
        reply_markup=back_kb
    )
    await NewsletterStates.waiting_for_text.set()

@dp.message_handler(state=NewsletterStates.waiting_for_text, content_types=['text', 'photo'])
async def get_newsletter_content(message: types.Message, state: FSMContext):
    """Получает контент для рассылки"""
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
        preview_text = f"📢 <b>Предпросмотр</b>\n\n{message.caption or 'Без подписи'}"
        await message.answer_photo(
            message.photo[-1].file_id,
            caption=preview_text,
            parse_mode="HTML"
        )
    else:
        newsletter_data['text'] = message.text
        newsletter_data.pop('photo', None)
        preview_text = f"📢 <b>Предпросмотр</b>\n\n{message.text}"
        await message.answer(preview_text, parse_mode="HTML")

    confirm_kb = InlineKeyboardMarkup(row_width=2)
    confirm_kb.add(
        InlineKeyboardButton("✅ Отправить", callback_data="send_news"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_news")
    )

    users = load_users_cached()
    await message.answer(
        f"👥 Будет отправлено: <b>{len(users)}</b>\n\nОтправить?",
        parse_mode="HTML",
        reply_markup=confirm_kb
    )
    await NewsletterStates.waiting_for_confirmation.set()

@dp.callback_query_handler(lambda c: c.data == "send_news", state=NewsletterStates.waiting_for_confirmation)
async def send_newsletter(callback_query: types.CallbackQuery, state: FSMContext):
    """Отправляет рассылку всем пользователям"""
    global last_newsletter_time
    
    await bot.answer_callback_query(callback_query.id)

    if not is_admin(callback_query.from_user.id):
        await state.finish()
        return

    # Защита от двойного клика
    if last_newsletter_time and (datetime.now() - last_newsletter_time).seconds < 10:
        await bot.send_message(
            callback_query.from_user.id,
            "⏳ Подождите 10 секунд перед новой рассылкой"
        )
        return
    
    last_newsletter_time = datetime.now()

    users = load_users_cached()
    status_msg = await bot.send_message(
        callback_query.from_user.id,
        f"📤 Отправка: 0/{len(users)}..."
    )

    sent = 0
    failed = 0
    
    newsletter_copy = newsletter_data.copy()
    newsletter_copy['sent_count'] = 0
    newsletter_copy['failed_count'] = 0

    for user in users:
        try:
            if 'photo' in newsletter_data:
                await bot.send_photo(
                    user["id"],
                    newsletter_data['photo'],
                    caption=newsletter_data.get('caption', '')
                )
            else:
                await bot.send_message(
                    user["id"],
                    newsletter_data['text']
                )
            sent += 1
            await asyncio.sleep(0.05)
            
            # Обновление прогресса каждые 5 пользователей с прогресс-баром
            if sent % 5 == 0:
                try:
                    progress = int((sent / len(users)) * 100)
                    bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
                    await status_msg.edit_text(
                        f"📤 <b>Отправка рассылки</b>\n\n"
                        f"[{bar}] {progress}%\n\n"
                        f"✅ Отправлено: {sent}/{len(users)}\n"
                        f"❌ Ошибок: {failed}",
                        parse_mode="HTML"
                    )
                except:
                    pass
                    
        except exceptions.BotBlocked:
            failed += 1
            log_warn(f"Пользователь {user['id']} заблокировал бота")
        except exceptions.UserDeactivated:
            failed += 1
            log_warn(f"Пользователь {user['id']} удалил аккаунт")
        except exceptions.ChatNotFound:
            failed += 1
        except Exception as e:
            failed += 1
            log_error(f"Ошибка отправки {user['id']}: {e}")

    newsletter_copy['sent_count'] = sent
    newsletter_copy['failed_count'] = failed
    newsletter_copy['total_users'] = len(users)
    
    newsletter_id = save_newsletter(newsletter_copy)

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}\n"
        f"👥 Всего: {len(users)}\n"
        f"🆔 ID: {newsletter_id}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("📋 Мои рассылки", callback_data="list_newsletters")
        )
    )

    newsletter_data.clear()
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "cancel_news", state=NewsletterStates.waiting_for_confirmation)
async def cancel_newsletter(callback_query: types.CallbackQuery, state: FSMContext):
    """Отменяет рассылку"""
    await bot.answer_callback_query(callback_query.id, "❌ Отменено")
    newsletter_data.clear()
    await state.finish()
    await bot.send_message(callback_query.from_user.id, "❌ Рассылка отменена.")
    await cmd_start(callback_query.message)

# ================ МОИ РАССЫЛКИ ================
@dp.message_handler(Text(equals="📋 Мои рассылки"))
async def list_newsletters(message: types.Message):
    """Показывает список рассылок"""
    if not is_admin(message.from_user.id):
        return
    
    newsletters = load_newsletters()
    if not newsletters:
        await message.answer("📭 У вас ещё нет рассылок", reply_markup=get_admin_kb())
        return
    
    for nl in newsletters[-5:][::-1]:
        date_str = nl.get('date', 'неизвестно')[:16]
        text = f"📅 <b>{date_str}</b>\n"
        text += f"👥 Отправлено: {nl.get('sent_count', 0)}/{nl.get('total_users', 0)}\n"
        if 'text' in nl:
            preview = nl['text'][:100] + ('...' if len(nl['text']) > 100 else '')
            text += f"💬 {preview}\n"
        elif 'photo' in nl:
            text += f"🖼 Фото: {nl.get('caption', 'Без текста')[:50]}\n"
        
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("❌ Удалить", callback_data=f"del_news_{nl['id']}")
        )
        await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('del_news_'))
async def delete_newsletter_callback(callback_query: types.CallbackQuery):
    """Запрашивает подтверждение удаления рассылки"""
    await bot.answer_callback_query(callback_query.id)
    
    if not is_admin(callback_query.from_user.id):
        return
    
    newsletter_id = callback_query.data.replace('del_news_', '')
    
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_del_{newsletter_id}"),
        InlineKeyboardButton("❌ Нет", callback_data="cancel_del")
    )
    
    await bot.send_message(
        callback_query.from_user.id,
        "❓ Точно удалить эту рассылку?",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('confirm_del_'))
async def confirm_delete(callback_query: types.CallbackQuery):
    """Подтверждает удаление рассылки"""
    newsletter_id = callback_query.data.replace('confirm_del_', '')
    delete_newsletter(newsletter_id)
    await bot.answer_callback_query(callback_query.id, "✅ Рассылка удалена")
    await callback_query.message.edit_text("✅ Рассылка удалена")

@dp.callback_query_handler(lambda c: c.data == "cancel_del")
async def cancel_delete(callback_query: types.CallbackQuery):
    """Отменяет удаление рассылки"""
    await bot.answer_callback_query(callback_query.id, "❌ Отменено")
    await callback_query.message.delete()

@dp.callback_query_handler(lambda c: c.data == "list_newsletters")
async def list_newsletters_callback(callback_query: types.CallbackQuery):
    """Показывает список рассылок (через callback)"""
    await bot.answer_callback_query(callback_query.id)
    await list_newsletters(callback_query.message)

# ================================================================================
# РАЗДЕЛЫ МЕНЮ
# ================================================================================

# ================ РАЗДЕЛ: АНАЛИЗ ВОДЫ ================
@dp.message_handler(Text(equals="🧪 Анализ воды"))
async def handle_analysis(message: types.Message):
    """Раздел: Анализ воды"""
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
    """Кнопка: Задать вопрос (в разделе Анализ воды)"""
    user_section[message.from_user.id] = "🧪 АНАЛИЗ ВОДЫ"
    await message.answer(
        "📝 Напишите ваш вопрос по воде или анализу — "
        "я передам его специалисту ДОНАКВА.",
        reply_markup=back_kb
    )

# ================ ПОДБОР СИСТЕМЫ ОЧИСТКИ ================
@dp.message_handler(Text(equals="💧 Подбор системы очистки"))
async def handle_select_system(message: types.Message):
    """Раздел: Подбор системы очистки"""
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
        "🏪 <b>Самовывоз</b> из нашего магазина\n\n"
        "👇 <b>Выберите ваши условия:</b>"
    )
    await message.answer(text, reply_markup=select_system_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Питьевая вода для дома"))
async def handle_drinking_water(message: types.Message):
    """Подраздел: Питьевая вода для дома"""
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
    """Подраздел: Квартира"""
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
        "✅ Я передам ваш запрос — инженер подберёт решение!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Частный дом"))
async def handle_house(message: types.Message):
    """Подраздел: Частный дом"""
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
    """Подраздел: Офис или бизнес"""
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
    """Подраздел: Производство"""
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
        "✅ Инженеры-технологи свяжутся с вами!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Просто интересуюсь"))
async def handle_curious(message: types.Message):
    """Подраздел: Просто интересуюсь"""
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
    """Раздел: Бассейны"""
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
        "🏪 <b>Самовывоз</b> из магазина по адресу:\n"
        f"📍 {ADDRESS}\n\n"
        "👇 <b>Выберите раздел:</b>"
    )
    await message.answer(text, reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🧪 Химия для бассейнов"))
async def handle_pool_chemistry(message: types.Message):
    """Подраздел: Химия для бассейнов"""
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
        "🏪 <b>Самовывоз</b> из нашего магазина!\n"
        "✅ Мы подберём дозировку и марку!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔧 Оборудование для бассейна"))
async def handle_pool_equipment(message: types.Message):
    """Подраздел: Оборудование для бассейна"""
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
        "🏪 <b>Самовывоз</b> из магазина\n"
        "✅ Подберём совместимый аналог или оригинал в наличии!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🚀 Комплекты для запуска"))
async def handle_pool_startup(message: types.Message):
    """Подраздел: Комплекты для запуска"""
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
        "🏪 <b>Самовывоз</b> из магазина\n"
        "✅ Соберём стартовый набор химии + тест-полоски!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🎯 Подбор под мой бассейн"))
async def handle_pool_custom(message: types.Message):
    """Подраздел: Индивидуальный подбор"""
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
        "🏪 <b>Самовывоз</b> из магазина\n"
        "✅ Подготовим коммерческое предложение!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ О КОМПАНИИ ================
@dp.message_handler(Text(equals="ℹ️ О компании ДОНАКВА"))
async def handle_about(message: types.Message):
    """Раздел: О компании"""
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
        "⏰ <b>Режим работы:</b>\n"
        "Пн-Пт: 9:00 - 15:00\n"
        "Сб, Вс: выходной\n\n"
        "🏪 <b>Самовывоз</b> товаров из магазина\n\n"
        f"📍 <b>Адрес:</b> {ADDRESS_LINK}\n"
        f"📞 <b>Телефон:</b> {PHONE_LINK}\n"
        "🌐 <b>Сайт:</b> www.donaqua.pro"
    )

    await send_logo(message.chat.id, text, site_kb, "HTML")

# ================ ПАРТНЁРСКАЯ ПРОГРАММА ================
@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    """Раздел: Партнёрская программа"""
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
        "• Техническая поддержка\n"
        "• Обучение и консультации\n"
        "• Маркетинговая поддержка\n"
        "• Совместные тендеры и проекты\n\n"
        "👇 <b>Выберите вашу сферу:</b>"
    )
    await message.answer(text, reply_markup=partner_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="Сантехник / монтажник"))
async def handle_partner_plumber(message: types.Message):
    """Подраздел: Сантехник / монтажник"""
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
    """Подраздел: Архитектор / дизайнер"""
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
    """Подраздел: Прораб / строитель"""
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
    """Подраздел: Бурильщик скважин"""
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
    """Подраздел: Другое"""
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
    """Кнопка: Оставить заявку"""
    user_section[message.from_user.id] = "📩 ЗАЯВКА"

    await message.answer(
        "📋 Опишите вашу задачу одним сообщением.\n\n"
        "Вы можете:\n"
        "• описать проблему с водой\n"
        "• запросить подбор оборудования\n"
        "• узнать стоимость монтажа\n"
        "• прикрепить фото/документы\n\n"
        "🏪 Товар — самовывоз из магазина\n\n"
        "✅ Специалист свяжется с вами!",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="🌐 На сайт"))
async def handle_site(message: types.Message):
    """Кнопка: На сайт"""
    await message.answer(
        "🌐 <b>Наш сайт:</b> www.donaqua.pro",
        reply_markup=back_kb,
        parse_mode="HTML"
    )

# ================================================================================
# ОБРАБОТКА СООБЩЕНИЙ ОТ ПОЛЬЗОВАТЕЛЕЙ
# ================================================================================

# ================ ОТВЕТ АДМИНА ЧЕРЕЗ REPLY ================
@dp.message_handler(lambda msg: is_admin(msg.from_user.id) and msg.reply_to_message is not None, content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'audio', 'sticker', 'location', 'contact'])
async def reply_to_user(message: types.Message):
    """Админ отвечает на заявку через reply с любыми файлами"""
    
    reply_text = message.reply_to_message.text or message.reply_to_message.caption
    if not reply_text:
        await message.answer("❌ Не могу определить, кому ответить")
        return

    match = re.search(r'🆔[:\s]*(\d+)', reply_text)
    if not match:
        await message.answer("❌ Не найден ID пользователя")
        return

    user_id = int(match.group(1))
    
    try:
        if message.text:
            await bot.send_message(
                user_id,
                f"📨 <b>Ответ от ДОНАКВА:</b>\n\n{message.text}",
                parse_mode="HTML"
            )
            admin_reply = message.text
            
        elif message.photo:
            await bot.send_photo(
                user_id,
                message.photo[-1].file_id,
                caption=f"📨 <b>Ответ от ДОНАКВА:</b>\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
            admin_reply = f"📸 Фото: {message.caption or 'без подписи'}"
            
        elif message.video:
            await bot.send_video(
                user_id,
                message.video.file_id,
                caption=f"📨 <b>Ответ от ДОНАКВА:</b>\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
            admin_reply = f"🎥 Видео: {message.caption or 'без подписи'}"
            
        elif message.voice:
            await bot.send_voice(
                user_id,
                message.voice.file_id,
                caption="📨 <b>Ответ от ДОНАКВА:</b> (голосовое сообщение)",
                parse_mode="HTML"
            )
            admin_reply = "🎤 Голосовое сообщение"
            
        elif message.video_note:
            await bot.send_video_note(
                user_id,
                message.video_note.file_id
            )
            admin_reply = "📹 Кружок"
            
        elif message.document:
            await bot.send_document(
                user_id,
                message.document.file_id,
                caption=f"📨 <b>Ответ от ДОНАКВА:</b>\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
            admin_reply = f"📎 Файл: {message.document.file_name}"
            
        elif message.audio:
            await bot.send_audio(
                user_id,
                message.audio.file_id,
                caption=f"📨 <b>Ответ от ДОНАКВА:</b>\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
            admin_reply = f"🎵 Аудио: {message.audio.title or message.audio.file_name}"
            
        elif message.sticker:
            await bot.send_sticker(
                user_id,
                message.sticker.file_id
            )
            admin_reply = "🎨 Стикер"
            
        elif message.location:
            await bot.send_location(
                user_id,
                message.location.latitude,
                message.location.longitude
            )
            admin_reply = "📍 Геопозиция"
            
        elif message.contact:
            await bot.send_contact(
                user_id,
                message.contact.phone_number,
                message.contact.first_name,
                last_name=message.contact.last_name or ""
            )
            admin_reply = f"👤 Контакт: {message.contact.first_name}"
            
        else:
            await message.answer("❌ Этот тип сообщения не поддерживается для ответа")
            return

        await message.answer(f"✅ Ответ отправлен пользователю ID: {user_id}")
        
        # Уведомляем других админов об отправленном ответе
        admin_name = message.from_user.full_name
        for admin_id in ADMIN_IDS:
            if admin_id != message.from_user.id:
                try:
                    await bot.send_message(
                        admin_id,
                        f"📤 <b>Отправлен ответ</b>\n"
                        f"👨‍💼 Админ: {admin_name}\n"
                        f"👤 Клиент ID: {user_id}\n"
                        f"💬 {admin_reply}",
                        parse_mode="HTML"
                    )
                except:
                    pass

    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")
        log_error(f"Ошибка отправки ответа: {e}")

# ================ УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК МЕДИАФАЙЛОВ ================
@dp.message_handler(content_types=['photo', 'video', 'voice', 'document'])
async def handle_media(message: types.Message):
    """Обрабатывает фото, видео, голосовые и документы от пользователей"""
    if is_admin(message.from_user.id) or not check_spam(message.from_user.id):
        return

    user = message.from_user
    source = user_source.get(user.id, None)
    
    # Определяем тип медиа
    if message.photo:
        media_type = "photo"
        section_default = "📸 ФОТО"
        media_text = f"📸 Фото: {message.caption or 'Без подписи'}"
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        section_default = "🎥 ВИДЕО"
        media_text = f"🎥 Видео: {message.caption or 'Без описания'}"
        file_id = message.video.file_id
    elif message.voice:
        media_type = "voice"
        section_default = "🎤 ГОЛОСОВОЕ"
        media_text = "🎤 Голосовое сообщение"
        file_id = message.voice.file_id
    elif message.document:
        media_type = "document"
        section_default = "📎 ДОКУМЕНТ"
        file_name = message.document.file_name or "Файл"
        media_text = f"📎 Файл: {file_name}\n💬 {message.caption or 'Без описания'}"
        file_id = message.document.file_id
    else:
        return

    section = user_section.get(user.id, section_default)
    
    # Проверка первого обращения
    requests_history = load_requests()
    is_first_time = str(user.id) not in requests_history
    
    # Сохраняем заявку
    request_data = {
        "user_id": user.id,
        "section": section,
        "message": media_text,
        "status": "NEW",
        "time": str(datetime.now()),
        "source": source
    }
    save_request(user.id, request_data, message.message_id, message.chat.id)

    # Формируем текст заявки
    request_text = format_request(
        user=user,
        section=section,
        message_text=media_text,
        status="NEW",
        source=source
    )

    # Кнопки для админа
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🟡 В работу", callback_data=f"work_{user.id}"),
        InlineKeyboardButton("🟢 Закрыть", callback_data=f"done_{user.id}"),
        InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user.id}")
    )

    # Отправляем всем админам
    try:
        await send_media_to_all_admins(media_type, file_id, request_text, kb)
        
        # Ответ пользователю с учётом рабочего времени
        auto_reply = get_auto_reply_text(is_first_time)
        await message.answer(auto_reply, parse_mode="HTML", reply_markup=main_kb)
            
    except Exception as e:
        log_error(f"Ошибка отправки медиа: {e}")
        await message.answer("✅ Спасибо! Ваше сообщение получено.", reply_markup=main_kb)

    # Очищаем раздел
    user_section.pop(user.id, None)

# ================ ТЕКСТОВЫЕ ЗАЯВКИ ================
@dp.message_handler()
async def handle_text(message: types.Message):
    """Обрабатывает текстовые сообщения от пользователей"""
    if message.text.startswith('/') or is_admin(message.from_user.id) or not check_spam(message.from_user.id):
        return

    user = message.from_user
    section = user_section.get(user.id, "📬 ОБЩАЯ ЗАЯВКА")
    source = user_source.get(user.id, None)
    
    # Проверяем, первое ли обращение
    requests_history = load_requests()
    is_first_time = str(user.id) not in requests_history
    
    # Сохраняем заявку
    request_data = {
        "user_id": user.id,
        "section": section,
        "message": message.text,
        "status": "NEW",
        "time": str(datetime.now()),
        "source": source
    }
    save_request(user.id, request_data, message.message_id, message.chat.id)

    # Формируем текст заявки
    request_text = format_request(
        user=user,
        section=section,
        message_text=message.text,
        status="NEW",
        source=source
    )

    # Кнопки для админа
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🟡 В работу", callback_data=f"work_{user.id}"),
        InlineKeyboardButton("🟢 Закрыть", callback_data=f"done_{user.id}"),
        InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user.id}")
    )

    try:
        # Отправляем всем админам
        await notify_all_admins(request_text, kb)
        
        # Автоответ с учётом рабочего времени
        auto_reply = get_auto_reply_text(is_first_time)
        await message.answer(auto_reply, parse_mode="HTML", reply_markup=main_kb)
            
    except Exception as e:
        log_error(f"Ошибка: {e}")
        await message.answer("✅ Спасибо! Ваша заявка получена.", reply_markup=main_kb)

    # Очищаем раздел
    user_section.pop(user.id, None)

# ================ ОБРАБОТЧИК КНОПКИ "ОТВЕТИТЬ" ================
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('reply_'))
async def process_reply_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие кнопки Ответить"""
    await bot.answer_callback_query(callback_query.id)

    if not is_admin(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "⛔ У вас нет прав администратора.")
        return

    user_id = int(callback_query.data.split('_')[1])
    reply_data[callback_query.from_user.id] = user_id

    await bot.send_message(
        callback_query.from_user.id,
        f"✏️ <b>Ответ пользователю ID: {user_id}</b>\n\n"
        f"Напишите ваш ответ в ответном сообщении (Reply) на это сообщение.",
        parse_mode="HTML"
    )

    await ReplyStates.waiting_for_reply.set()

@dp.message_handler(state=ReplyStates.waiting_for_reply)
async def handle_reply_text(message: types.Message, state: FSMContext):
    """Обрабатывает текст ответа админа"""
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
            f"📨 <b>Ответ от ДОНАКВА:</b>\n\n{reply_text}",
            parse_mode="HTML"
        )

        await message.answer(f"✅ Ответ отправлен пользователю ID: {user_id}")

        # Уведомляем других админов
        admin_name = message.from_user.full_name
        for admin_id in ADMIN_IDS:
            if admin_id != message.from_user.id:
                try:
                    await bot.send_message(
                        admin_id,
                        f"📤 <b>Отправлен ответ</b>\n"
                        f"👨‍💼 Админ: {admin_name}\n"
                        f"👤 Клиент ID: {user_id}\n"
                        f"💬 {reply_text}",
                        parse_mode="HTML"
                    )
                except:
                    pass

    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")
        log_error(f"Ошибка отправки ответа: {e}")

    reply_data.pop(message.from_user.id, None)
    await state.finish()

# ================ ОБРАБОТЧИК СТАТУСОВ ЗАЯВОК ================
@dp.callback_query_handler(lambda c: c.data.startswith('work_'))
async def set_work(callback: types.CallbackQuery):
    """Устанавливает статус 'В работе'"""
    user_id = int(callback.data.split('_')[1])
    
    requests = load_requests()
    if str(user_id) in requests:
        requests[str(user_id)]['status'] = 'WORK'
        requests[str(user_id)]['taken_by'] = callback.from_user.id
        requests[str(user_id)]['taken_at'] = str(datetime.now())
        with open(REQUESTS_FILE, 'w') as f:
            json.dump(requests, f, indent=2)
    
    admin_name = callback.from_user.full_name
    await callback.answer(f"✅ Заявка в работе у {admin_name}")
    
    # Обновляем кнопки
    new_kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(f"🟠 В работе ({admin_name[:15]})", callback_data=f"info_work"),
        InlineKeyboardButton("🟢 Закрыть", callback_data=f"done_{user_id}"),
        InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user_id}")
    )
    
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except:
        pass

@dp.callback_query_handler(lambda c: c.data.startswith('done_'))
async def set_done(callback: types.CallbackQuery):
    """Устанавливает статус 'Закрыта'"""
    user_id = int(callback.data.split('_')[1])
    
    requests = load_requests()
    if str(user_id) in requests:
        requests[str(user_id)]['status'] = 'DONE'
        requests[str(user_id)]['closed_by'] = callback.from_user.id
        requests[str(user_id)]['closed_at'] = str(datetime.now())
        with open(REQUESTS_FILE, 'w') as f:
            json.dump(requests, f, indent=2)
    
    admin_name = callback.from_user.full_name
    await callback.answer(f"✅ Заявка закрыта ({admin_name})")
    
    # Обновляем кнопки
    new_kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(f"🟢 Закрыта ({admin_name[:15]})", callback_data=f"info_done"),
        InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user_id}")
    )
    
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except:
        pass

@dp.callback_query_handler(lambda c: c.data.startswith('info_'))
async def info_callback(callback: types.CallbackQuery):
    """Информационные кнопки (не делают ничего)"""
    status = callback.data.replace('info_', '')
    if status == 'work':
        await callback.answer("🟠 Заявка в работе")
    elif status == 'done':
        await callback.answer("🟢 Заявка закрыта")

# ================================================================================
# АВТОКОНТРОЛЬ И НАПОМИНАНИЯ
# ================================================================================

async def auto_control():
    """Автоматический контроль заявок и напоминания"""
    last_cleanup = datetime.now().date()
    
    while True:
        await asyncio.sleep(60)  # Проверка каждую минуту
        
        requests = load_requests()
        now = datetime.now()
        
        # Очистка старых заявок раз в день
        if now.date() != last_cleanup:
            cleanup_old_requests()
            last_cleanup = now.date()
        
        for user_id_str, data in requests.items():
            try:
                user_id = int(user_id_str)
                status = data.get('status', 'NEW')
                reminded = data.get('reminded', False)
                admin_reminded = data.get('admin_reminded', False)
                request_time = datetime.fromisoformat(data['time'])
                delta = now - request_time
                
                # Напоминание админам через 15 минут (только в рабочее время и один раз)
                if status == 'NEW' and delta > timedelta(minutes=15) and not admin_reminded and is_working_hours():
                    message_link = data.get('message_link', '')
                    if message_link:
                        await notify_all_admins(
                            f"⚠️ <a href='{message_link}'>Заявка от пользователя {user_id}</a> без ответа более 15 минут!\n"
                            f"👆 Нажмите на ссылку, чтобы перейти к сообщению"
                        )
                    else:
                        await notify_all_admins(
                            f"⚠️ Заявка от пользователя {user_id} без ответа более 15 минут!\n"
                            f"🔍 ID для поиска: <code>{user_id}</code>"
                        )
                    data['admin_reminded'] = True
                    save_request(user_id, data)
                    log_info(f"Напоминание админам отправлено для заявки {user_id}")
                
                # Напоминание пользователю через 24 часа (только ОДИН РАЗ!)
                if status != 'DONE' and delta > timedelta(hours=24) and not reminded:
                    try:
                        await bot.send_message(
                            user_id,
                            "🔔 Напоминаем о вашей заявке в ДОНАКВА.\n"
                            "Всё ещё актуально? Напишите нам, и мы ответим!"
                        )
                        data['reminded'] = True
                        save_request(user_id, data)
                        log_info(f"Напоминание отправлено пользователю {user_id}")
                    except Exception as e:
                        log_error(f"Ошибка отправки пользователю {user_id}: {e}")
            except Exception as e:
                log_error(f"Ошибка обработки пользователя {user_id_str}: {e}")

# ================================================================================
# ЗАПУСК БОТА
# ================================================================================

async def start_bot_with_retry():
    """Запускает бота с обработкой ошибок сети и повторными попытками"""
    retries = 0
    max_retries = 10
    base_delay = 5

    while retries < max_retries:
        try:
            log_info(f"Попытка запуска #{retries + 1}...")
            await bot.delete_webhook(drop_pending_updates=True)
            
            await asyncio.gather(
                dp.start_polling(),
                run_web_server(),
                auto_control()
            )
            break

        except (aiohttp.client_exceptions.ClientConnectorError, 
                aiohttp.client_exceptions.ServerDisconnectedError,
                exceptions.NetworkError) as e:
            retries += 1
            wait_time = base_delay * (2 ** (retries - 1))
            log_warn(f"Ошибка сети: {e}. Повтор через {wait_time} сек (попытка {retries}/{max_retries})")
            await asyncio.sleep(wait_time)

        except exceptions.RetryAfter as e:
            wait_time = e.retry_after + 1
            log_warn(f"Flood control: нужно подождать {wait_time} сек.")
            await asyncio.sleep(wait_time)

        except exceptions.TelegramAPIError as e:
            if "Bad Gateway" in str(e) or "Gateway" in str(e):
                retries += 1
                wait_time = base_delay * (2 ** (retries - 1))
                log_warn(f"Ошибка шлюза (Bad Gateway): {e}. Повтор через {wait_time} сек")
                await asyncio.sleep(wait_time)
            else:
                raise e

        except Exception as e:
            log_error(f"Критическая ошибка: {e}")
            raise e

    else:
        log_error("Не удалось запустить бота после нескольких попыток.")

# ================ ВЕБ-СЕРВЕР ================
async def handle_web(request):
    """Обработчик веб-запросов для healthcheck"""
    working_status = "🟢 Рабочее время" if is_working_hours() else "🔴 Нерабочее время"
    return web.Response(
        text=f"🤖 Бот ДОНАКВА работает!\n⏰ {working_status}\n👨‍💼 Админов: {len(ADMIN_IDS)}"
    )

async def run_web_server():
    """Запускает веб-сервер для хостинга"""
    app = web.Application()
    app.router.add_get('/', handle_web)
    app.router.add_get('/health', handle_web)

    port = int(os.environ.get('PORT', 10000))
    log_info(f"Веб-сервер запущен на порту {port}")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    await asyncio.Event().wait()

# ================ ТОЧКА ВХОДА ================
if __name__ == "__main__":
    try:
        log_info("=" * 50)
        log_info("🚀 Запуск бота ДОНАКВА")
        log_info(f"👨‍💼 Админов: {len(ADMIN_IDS)}")
        for admin_id in ADMIN_IDS:
            role = "Главный (техподдержка)" if admin_id == 488352806 else "Менеджер"
            log_info(f"   • {admin_id} — {role}")
        log_info(f"⏰ Рабочее время: Пн-Пт {WORKING_HOURS['start']}:00-{WORKING_HOURS['end']}:00")
        log_info(f"🕐 Текущее время: {get_local_time().strftime('%d.%m.%Y %H:%M')}")
        log_info(f"📊 Статус: {'Рабочее время' if is_working_hours() else 'Нерабочее время'}")
        log_info("=" * 50)
        asyncio.run(start_bot_with_retry())
    except KeyboardInterrupt:
        log_info("Бот остановлен")
    except Exception as e:
        log_error(f"Неисправимая ошибка: {e}")
