import asyncio
import os
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

# ================ КЛАВИАТУРЫ ================
# Главное меню
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

# Кнопка "Назад"
back_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 Назад в главное меню")]],
    resize_keyboard=True
)

# Клавиатура для раздела "Анализ воды"
analysis_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Задать вопрос")],
        [KeyboardButton(text="🌐 На сайт")],
        [KeyboardButton(text="🔙 Назад в главное меню")],
    ],
    resize_keyboard=True
)

# Клавиатура для раздела "Бассейны"
pool_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Химия для бассейнов"), KeyboardButton(text="Оборудование для бассейна")],
        [KeyboardButton(text="Комплекты для запуска"), KeyboardButton(text="Подбор под мой бассейн")],
        [KeyboardButton(text="Оставить заявку"), KeyboardButton(text="🔙 Назад в главное меню")],
    ],
    resize_keyboard=True
)

# Клавиатура для раздела "Подбор системы очистки"
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

# Клавиатура для раздела "Партнёрская программа"
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

# Клавиатура с ссылкой на сайт
site_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌐 На сайт")],
        [KeyboardButton(text="🔙 Назад в главное меню")],
    ],
    resize_keyboard=True
)

# ================ URL ЛОГОТИПА ================
# Логотип с вашего сайта
LOGO_URL = "https://donaqua.pro/wp-content/uploads/2021/04/logo-1.png"

# ================ ОБРАБОТЧИКИ КОМАНД ================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start с логотипом"""
    
    # Текст приветствия
    welcome_text = (
        "🌊 <b>Добро пожаловать в ДОНАКВА!</b>\n\n"
        "Мы — профессиональная команда специалистов по очистке воды, "
        "насосному оборудованию и бассейнам.\n\n"
        "🔹 <b>20+ лет</b> опыта\n"
        "🔹 <b>1000+</b> реализованных проектов\n"
        "🔹 Индивидуальный подход к каждому клиенту\n\n"
        "Выберите нужный раздел в меню ниже 👇"
    )
    
    try:
        # Отправляем логотип с подписью
        await message.answer_photo(
            photo=LOGO_URL,
            caption=welcome_text,
            reply_markup=main_kb,
            parse_mode="HTML"
        )
    except Exception as e:
        # Если не получилось отправить логотип, отправляем просто текст
        print(f"Ошибка отправки логотипа: {e}")
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
        "Анализ воды — самый первый и правильный шаг в подборе водоочистного оборудования. "
        "Только на основании химического и бактериологического анализов выявляются характер "
        "и степень загрязненности источника воды.\n\n"
        "✅ Результаты анализа позволят сделать подбор водоочистного оборудования "
        "максимально адаптированным к существующим реалиям и сэкономят Ваши средства.\n\n"
        "⏱ <b>Срок выполнения:</b> 2–5 рабочих дней\n"
        "💰 <b>Стоимость:</b> 3500 руб.\n\n"
        "📍 <b>Как сдать анализ:</b>\n"
        "ДНР, г. Донецк, ул. Щорса 38, магазин ДОНАКВА\n"
        "📞 +7 949 321‑98‑00\n\n"
        "📋 <b>Как подготовить образец:</b>\n"
        "• пластиковая бутылка 1–1,5 л\n"
        "• перед набором слейте воду 2–3 минуты\n"
        "• наберите свежую воду без газа\n"
        "• плотно закройте бутылку\n\n"
        "После анализа мы подробно объясним результаты и предложим оптимальное решение!"
    )
    await message.answer(text, reply_markup=analysis_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔄 Задать вопрос"))
async def handle_analysis_question(message: types.Message):
    """Задать вопрос по анализу воды"""
    await message.answer(
        "📝 Напишите ваш вопрос по воде или анализу одним сообщением — "
        "я передам его специалисту ДОНАКВА. Мы ответим вам в ближайшее время!",
        reply_markup=back_kb
    )

# ================ РАЗДЕЛ: ПОДБОР СИСТЕМЫ ОЧИСТКИ ================
@dp.message_handler(Text(equals="💧 Подбор системы очистки"))
async def handle_select_system(message: types.Message):
    """Выбор условий для подбора системы"""
    text = (
        "💧 <b>Подбор системы очистки воды</b>\n\n"
        "Мы предлагаем широкий выбор технических решений, основанных на передовых технологиях:\n"
        "• Мембранные технологии (обратный осмос)\n"
        "• Оборудование фильтрации\n"
        "• Специальные химреагенты\n"
        "• Безреагентные системы\n\n"
        "Выберите, для каких условий нужна очистка воды:"
    )
    await message.answer(text, reply_markup=select_system_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Питьевая вода для дома", "Квартира", "Частный дом", "Офис или бизнес", "Производство", "Просто интересуюсь"]))
async def handle_select_system_option(message: types.Message):
    """Обработка выбора условий"""
    option = message.text
    base = (
        "📋 Опишите вашу ситуацию одним сообщением:\n"
        "• откуда берете воду (скважина, колодец, городской водопровод)\n"
        "• какие проблемы (запах, вкус, накипь, ржавчина, мутность)\n"
        "• сколько человек в семье/сотрудников\n"
        "• примерный расход воды\n\n"
        "Я передам информацию специалисту ДОНАКВА для подбора оптимального решения!"
    )
    await message.answer(f"✅ <b>Вы выбрали:</b> {option}\n\n{base}", reply_markup=back_kb, parse_mode="HTML")

# ================ РАЗДЕЛ: БАССЕЙНЫ ================
@dp.message_handler(Text(equals="🏊 Химия и оборудование для бассейнов"))
async def handle_pool(message: types.Message):
    """Информация о бассейнах"""
    text = (
        "🏊 <b>Химия и оборудование для бассейнов</b>\n\n"
        "У нас есть всё для вашего бассейна:\n"
        "• Химия для дезинфекции и ухода\n"
        "• Фильтровальные установки\n"
        "• Насосы и гидромассажное оборудование\n"
        "• Комплекты для запуска бассейна\n"
        "• Аксессуары и принадлежности\n\n"
        "Поможем подобрать оборудование под ваш бассейн и бюджет!"
    )
    await message.answer(text, reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Оставить заявку", "Подбор под мой бассейн"]))
async def handle_pool_request(message: types.Message):
    """Заявка по бассейну"""
    await message.answer(
        "🏊 Опишите ваш бассейн:\n"
        "• объём (м³)\n"
        "• тип (частный, общественный, спа)\n"
        "• текущая проблема или задача\n\n"
        "Напишите всё одним сообщением — мы подберем лучшее решение!",
        reply_markup=back_kb
    )

# ================ РАЗДЕЛ: О КОМПАНИИ (ОБНОВЛЕН) ================
@dp.message_handler(Text(equals="ℹ️ О компании ДОНАКВА"))
async def handle_about(message: types.Message):
    """Информация о компании с сайта donaqua.pro"""
    
    about_text = (
        "🏢 <b>О компании ДОНАКВА</b>\n\n"
        "Высококвалифицированный штат специалистов быстро и качественно осуществит: "
        "подбор, монтаж и сервисное обслуживание оборудования по очистке воды для "
        "квартиры, коттеджа, ресторана или промышленного предприятия.\n\n"
        "🔧 <b>Наши направления:</b>\n"
        "• Промышленные системы подготовки и очистки воды\n"
        "• Коммерческие системы очистки воды\n"
        "• Бытовые системы подготовки и очистки воды\n\n"
        "🧪 <b>Комплексный анализ воды</b>\n"
        "Анализ воды — самый первый и правильный шаг в подборе водоочистного оборудования. "
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
    
    try:
        # Отправляем логотип с информацией о компании
        await message.answer_photo(
            photo=LOGO_URL,
            caption=about_text,
            reply_markup=site_kb,
            parse_mode="HTML"
        )
    except Exception as e:
        # Если не получилось отправить логотип, отправляем просто текст
        print(f"Ошибка отправки логотипа: {e}")
        await message.answer(about_text, reply_markup=site_kb, parse_mode="HTML")

# ================ РАЗДЕЛ: ПАРТНЁРСКАЯ ПРОГРАММА ================
@dp.message_handler(Text(equals="🤝 Партнёрская программа"))
async def handle_partner(message: types.Message):
    """Партнёрская программа"""
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
        "• Техническую поддержку\n"
        "• Обучение и консультации\n"
        "• Маркетинговую поддержку\n\n"
        "Выберите вашу сферу деятельности:"
    )
    await message.answer(text, reply_markup=partner_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Сантехник / монтажник", "Архитектор / дизайнер", "Прораб / строитель", "Бурильщик скважин", "Другое"]))
async def handle_partner_option(message: types.Message):
    """Выбор сферы партнёра"""
    role = message.text
    await message.answer(
        f"✅ <b>Вы выбрали:</b> {role}\n\n"
        f"📋 Опишите, чем вы занимаетесь и какой формат сотрудничества вам интересен.\n\n"
        f"Мы свяжемся с вами и обсудим детали!",
        reply_markup=back_kb,
        parse_mode="HTML"
    )

# ================ ЗАЯВКИ ================
@dp.message_handler(Text(equals="📩 Оставить заявку"))
async def handle_request(message: types.Message):
    """Общая заявка"""
    await message.answer(
        "📋 Опишите вашу задачу одним сообщением.\n"
        "Вы также можете прикрепить фото или документы.\n\n"
        "Наш специалист свяжется с вами в ближайшее время!",
        reply_markup=back_kb
    )

# ================ САЙТ ================
@dp.message_handler(Text(equals="🌐 На сайт"))
async def handle_site(message: types.Message):
    """Ссылка на сайт"""
    text = (
        "🌐 <b>Наш сайт:</b> www.donaqua.pro\n\n"
        "На сайте вы можете:\n"
        "• Ознакомиться с каталогом оборудования\n"
        "• Узнать актуальные цены\n"
        "• Посмотреть наши работы\n"
        "• Заказать обратный звонок"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

# ================ ОБРАБОТЧИК ФОТО ================
@dp.message_handler(content_types=ContentType.PHOTO)
async def handle_photo(message: types.Message):
    """Обработка фото (заявки с изображениями)"""
    
    user = message.from_user
    user_info = f"{user.full_name} (@{user.username}) id={user.id}"
    
    header = f"📸 Новая заявка с фото от пользователя:\n\n👤 {user_info}"
    
    # Получаем фото максимального размера
    photo = message.photo[-1]
    
    try:
        # Отправляем фото и текст админу
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=f"{header}\n\n💬 Подпись: {message.caption or 'Без подписи'}"
        )
        
        await message.answer(
            "✅ Спасибо! Ваша заявка с фото отправлена.\nМы свяжемся с вами.",
            reply_markup=main_kb
        )
    except Exception as e:
        print(f"Ошибка отправки фото админу: {e}")
        await message.answer(
            "✅ Спасибо! Ваша заявка получена.",
            reply_markup=main_kb
        )

# ================ ОБРАБОТЧИК ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ ================
@dp.message_handler()
async def handle_free_text(message: types.Message):
    """Обработка всех текстовых сообщений (заявки, вопросы)"""
    
    # Пропускаем команды
    if message.text.startswith('/'):
        return
    
    # Отправляем заявку админу
    user = message.from_user
    user_info = f"{user.full_name} (@{user.username}) id={user.id}"
    
    header = "📬 Новая заявка от пользователя:\n\n"
    text = header + f"👤 {user_info}\n\n💬 Текст:\n{message.text}"
    
    try:
        # Пробуем отправить уведомление админу
        await bot.send_message(chat_id=ADMIN_ID, text=text)
        
        # Отправляем подтверждение пользователю
        await message.answer(
            "✅ Спасибо! Ваша заявка отправлена.\n"
            "Мы свяжемся с вами в ближайшее время.",
            reply_markup=main_kb
        )
        
    except Exception as e:
        # Если не получилось отправить админу - логируем ошибку
        print(f"Ошибка отправки админу {ADMIN_ID}: {e}")
        print(f"Убедитесь, что админ (ID: {ADMIN_ID}) написал боту /start")
        
        # Но пользователю всё равно отвечаем
        await message.answer(
            "✅ Спасибо! Ваша заявка получена.\n"
            "Мы свяжемся с вами в ближайшее время.",
            reply_markup=main_kb
        )

# ================ ЗАПУСК БОТА ================
async def main():
    """Главная функция запуска"""
    print(f"🤖 Бот ДОНАКВА запущен")
    print(f"🔑 Токен: {API_TOKEN[:10]}...")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print(f"🖼 Логотип: {LOGO_URL}")
    print("🔄 Ожидание сообщений...")
    
    # Удаляем вебхук (на случай если был)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем поллинг
    await dp.start_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
