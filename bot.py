import asyncio
import os
import base64
from io import BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.types.message import ContentType

# ================ НАСТРОЙКИ ================
# Получаем токен из переменных окружения
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 488352806  # ID админа для отправки уведомлений

if not API_TOKEN:
    raise ValueError("ERROR: BOT_TOKEN not set in environment variables!")

# ================ ИНИЦИАЛИЗАЦИЯ ================
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ================ ЛОГОТИП В ВИДЕ BASE64 ================
LOGO_BASE64 = "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"

async def send_logo(chat_id, caption, reply_markup=None, parse_mode="HTML"):
    """Отправляет логотип из base64"""
    try:
        image_data = base64.b64decode(LOGO_BASE64)
        image_io = BytesIO(image_data)
        image_io.name = 'logo.png'
        
        await bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(image_io),
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки логотипа: {e}")
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
        [KeyboardButton(text="📋 Оставить заявку"), KeyboardButton(text="🔙 Назад в главное меню")],
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

# ================ ОБРАБОТЧИКИ КОМАНД ================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start с логотипом"""
    
    welcome_text = (
        "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
        "Мы — профессиональная команда специалистов по очистке воды, "
        "насосному оборудованию и бассейнам.\n\n"
        "🔹 <b>20+ лет</b> опыта\n"
        "🔹 <b>1000+</b> реализованных проектов\n"
        "🔹 Индивидуальный подход к каждому клиенту\n\n"
        "Выберите нужный раздел в меню ниже 👇"
    )
    
    success = await send_logo(
        chat_id=message.chat.id,
        caption=welcome_text,
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    
    if not success:
        text = (
            "🌊 <b>ДОНАКВА</b> — фильтры для воды, насосы, бассейны.\n\n"
            "Адрес магазина:\n"
            "ДНР, г. Донецк, ул. Щорса 38, магазин ДОНАКВА\n"
            "Телефон: +7 949 321‑98‑00\n\n"
            "Выберите нужный раздел:"
        )
        await message.answer(text, reply_markup=main_kb, parse_mode="HTML")

# ================ НАВИГАЦИЯ ================
@dp.message_handler(Text(equals="🔙 Назад в главное меню"))
async def handle_back_to_main(message: types.Message):
    """Возврат в главное меню"""
    await cmd_start(message)

# ================ РАЗДЕЛ: АНАЛИЗ ВОДЫ ================
@dp.message_handler(Text(equals="🧪 Анализ воды"))
async def handle_analysis(message: types.Message):
    """Информация об анализе воды"""
    text = (
        "🧪 <b>Анализ воды</b>\n\n"
        "Анализ воды — самый первый и правильный шаг в подборе водоочистного оборудования.\n\n"
        "⏱ <b>Срок выполнения:</b> 2–5 рабочих дней\n"
        "💰 <b>Стоимость:</b> 3500 руб.\n\n"
        "📍 <b>Адрес:</b>\n"
        "ДНР, г. Донецк, ул. Щорса 38, магазин ДОНАКВА\n"
        "📞 +7 949 321‑98‑00\n\n"
        "📋 <b>Как подготовить образец:</b>\n"
        "• пластиковая бутылка 1–1,5 л\n"
        "• перед набором слейте воду 2–3 минуты\n"
        "• наберите свежую воду без газа\n"
        "• плотно закройте бутылку"
    )
    await message.answer(text, reply_markup=analysis_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔄 Задать вопрос"))
async def handle_analysis_question(message: types.Message):
    """Задать вопрос по анализу воды"""
    await message.answer(
        "📝 Напишите ваш вопрос по воде или анализу одним сообщением — "
        "я передам его специалисту ДОНАКВА.",
        reply_markup=back_kb
    )

# ================ РАЗДЕЛ: ПОДБОР СИСТЕМЫ ОЧИСТКИ ================
@dp.message_handler(Text(equals="💧 Подбор системы очистки"))
async def handle_select_system(message: types.Message):
    """Выбор условий для подбора системы"""
    text = (
        "💧 <b>Подбор системы очистки воды</b>\n\n"
        "Выберите, для каких условий нужна очистка воды:"
    )
    await message.answer(text, reply_markup=select_system_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Питьевая вода для дома", "Квартира", "Частный дом", "Офис или бизнес", "Производство", "Просто интересуюсь"]))
async def handle_select_system_option(message: types.Message):
    """Обработка выбора условий"""
    option = message.text
    base = (
        "📋 Опишите вашу ситуацию одним сообщением:\n"
        "• откуда берете воду\n"
        "• какие проблемы (запах, вкус, накипь, ржавчина)\n"
        "• сколько человек в семье/сотрудников\n\n"
        "Я передам информацию специалисту ДОНАКВА!"
    )
    await message.answer(f"✅ <b>Вы выбрали:</b> {option}\n\n{base}", reply_markup=back_kb, parse_mode="HTML")

# ================ РАЗДЕЛ: БАССЕЙНЫ ================
@dp.message_handler(Text(equals="🏊 Химия и оборудование для бассейнов"))
async def handle_pool(message: types.Message):
    """Главное меню бассейнов"""
    text = (
        "🏊 <b>Химия и оборудование для бассейнов</b>\n\n"
        "👇 <b>Выберите, что вас интересует:</b>"
    )
    await message.answer(text, reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🧪 Химия для бассейнов"))
async def handle_pool_chemistry(message: types.Message):
    """Заявка на химию для бассейна"""
    text = (
        "🧪 <b>Химия для бассейнов</b>\n\n"
        "Опишите, какая химия вам необходима:\n\n"
        "• <b>Тип химии</b> (хлор, бром, активный кислород, альгицид, pH-корректор)\n"
        "• <b>Объём бассейна</b> (в м³)\n"
        "• <b>Тип бассейна</b> (частный, общественный, каркасный)\n"
        "• <b>Необходимое количество</b>\n"
        "• <b>Текущая проблема</b>\n\n"
        "📌 <i>Пример: «Нужен хлор в таблетках для бассейна 25 м³, зелёная вода»</i>\n\n"
        "Напишите всё одним сообщением!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔧 Оборудование для бассейна"))
async def handle_pool_equipment(message: types.Message):
    """Заявка на оборудование для бассейна"""
    text = (
        "🔧 <b>Оборудование для бассейна</b>\n\n"
        "Опишите, какое оборудование вам необходимо:\n\n"
        "• <b>Тип оборудования</b> (фильтр, насос, нагреватель, лестница)\n"
        "• <b>Объём бассейна</b> (в м³)\n"
        "• <b>Что случилось?</b> (поломка, замена, новый монтаж)\n"
        "• <b>Бренд</b> (если есть предпочтения)\n"
        "• <b>Бюджет</b>\n\n"
        "📌 <i>Пример: «Нужен песочный фильтр для бассейна 35 м³, старый сломался»</i>\n\n"
        "Напишите всё одним сообщением!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🚀 Комплекты для запуска"))
async def handle_pool_startup(message: types.Message):
    """Заявка на комплект для запуска бассейна"""
    text = (
        "🚀 <b>Комплекты для запуска бассейна</b>\n\n"
        "Опишите ваш бассейн:\n\n"
        "• <b>Объём бассейна</b> (в м³)\n"
        "• <b>Тип бассейна</b> (новый, после зимы)\n"
        "• <b>Тип фильтрации</b>\n\n"
        "📌 <i>Пример: «Нужен комплект для запуска бассейна 45 м³, песочный фильтр»</i>\n\n"
        "Напишите одним сообщением!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🎯 Подбор под мой бассейн"))
async def handle_pool_custom(message: types.Message):
    """Индивидуальный подбор под бассейн"""
    text = (
        "🎯 <b>Индивидуальный подбор</b>\n\n"
        "Опишите вашу ситуацию:\n\n"
        "• <b>Объём бассейна</b> (м³)\n"
        "• <b>Тип бассейна</b>\n"
        "• <b>Какая задача?</b>\n"
        "• <b>Что именно нужно?</b>\n"
        "• <b>Бюджет и сроки</b>\n\n"
        "📌 <i>Пример: «Бассейн 60 м³, частный. Нужен насос и дозация хлора, бюджет до 150 000 руб.»</i>\n\n"
        "Напишите всё одним сообщением!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ РАЗДЕЛ: О КОМПАНИИ ================
@dp.message_handler(Text(equals="ℹ️ О компании ДОНАКВА"))
async def handle_about(message: types.Message):
    """Информация о компании с логотипом"""
    
    about_text = (
        "🏢 <b>О компании ДОНАКВА</b>\n\n"
        "Высококвалифицированный штат специалистов быстро и качественно осуществит: "
        "подбор, монтаж и сервисное обслуживание оборудования по очистке воды.\n\n"
        "📍 <b>Адрес:</b> г. Донецк, ул. Щорса, д. 38\n"
        "📞 <b>Телефон:</b> +7 949 321‑98‑00\n"
        "🌐 <b>Сайт:</b> www.donaqua.pro"
    )
    
    success = await send_logo(
        chat_id=message.chat.id,
        caption=about_text,
        reply_markup=site_kb,
        parse_mode="HTML"
    )
    
    if not success:
        await message.answer(about_text, reply_markup=site_kb, parse_mode="HTML")

# ================ РАЗДЕЛ: ПАРТНЁРСКАЯ ПРОГРАММА ================
@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    """Партнёрская программа"""
    text = (
        "🤝 <b>Партнёрская программа ДОНАКВА</b>\n\n"
        "Выберите вашу сферу деятельности:"
    )
    await message.answer(text, reply_markup=partner_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Сантехник / монтажник", "Архитектор / дизайнер", "Прораб / строитель", "Бурильщик скважин", "Другое"]))
async def handle_partner_option(message: types.Message):
    """Выбор сферы партнёра"""
    role = message.text
    await message.answer(
        f"✅ <b>Вы выбрали:</b> {role}\n\n"
        f"📋 Опишите, чем вы занимаетесь и какой формат сотрудничества вам интересен.",
        reply_markup=back_kb,
        parse_mode="HTML"
    )

# ================ ЗАЯВКИ ================
@dp.message_handler(Text(equals="📩 Оставить заявку"))
async def handle_request(message: types.Message):
    """Общая заявка"""
    await message.answer(
        "📋 Опишите вашу задачу одним сообщением.\n"
        "Вы также можете прикрепить фото.",
        reply_markup=back_kb
    )

@dp.message_handler(Text(equals="📋 Оставить заявку"))
async def handle_pool_request(message: types.Message):
    """Заявка из раздела бассейны"""
    await message.answer(
        "📋 Опишите вашу задачу одним сообщением.",
        reply_markup=back_kb
    )

# ================ САЙТ ================
@dp.message_handler(Text(equals="🌐 На сайт"))
async def handle_site(message: types.Message):
    """Ссылка на сайт"""
    await message.answer("🌐 Наш сайт: www.donaqua.pro", reply_markup=back_kb, parse_mode="HTML")

# ================ ОБРАБОТЧИК ФОТО ================
@dp.message_handler(content_types=ContentType.PHOTO)
async def handle_photo(message: types.Message):
    """Обработка фото"""
    user = message.from_user
    user_info = f"{user.full_name} (@{user.username}) id={user.id}"
    photo = message.photo[-1]
    
    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=f"📸 Новая заявка с фото:\n👤 {user_info}\n\n💬 {message.caption or 'Без подписи'}"
        )
        await message.answer("✅ Спасибо! Ваша заявка с фото отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        await message.answer("✅ Спасибо! Ваша заявка получена.", reply_markup=main_kb)

# ================ ОБРАБОТЧИК ТЕКСТА ================
@dp.message_handler()
async def handle_free_text(message: types.Message):
    """Обработка всех текстовых сообщений"""
    
    if message.text.startswith('/'):
        return
    
    user = message.from_user
    user_info = f"{user.full_name} (@{user.username}) id={user.id}"
    text = f"📬 Новая заявка:\n\n👤 {user_info}\n\n💬 {message.text}"
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text)
        await message.answer("✅ Спасибо! Ваша заявка отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")
        await message.answer("✅ Спасибо! Ваша заявка получена.", reply_markup=main_kb)

# ================ ВЕБ-СЕРВЕР ДЛЯ RENDER ================
from aiohttp import web

async def handle(request):
    return web.Response(text="🤖 Telegram бот ДОНАКВА работает!")

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
    print(f"🔑 Токен: {API_TOKEN[:10]}...")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print(f"🖼 Логотип: встроенный (base64)")
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    polling_task = asyncio.create_task(dp.start_polling())
    web_task = asyncio.create_task(run_web_server())
    
    await asyncio.gather(polling_task, web_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
