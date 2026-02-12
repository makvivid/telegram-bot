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
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 488352806

if not API_TOKEN:
    raise ValueError("ERROR: BOT_TOKEN not set in environment variables!")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ================ ЛОГОТИП ================
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

# ================ СТАРТ ================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
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
    
    success = await send_logo(message.chat.id, welcome_text, main_kb, "HTML")
    if not success:
        await message.answer(welcome_text, reply_markup=main_kb, parse_mode="HTML")

# ================ НАЗАД ================
@dp.message_handler(Text(equals="🔙 Назад в главное меню"))
async def back_to_main(message: types.Message):
    await cmd_start(message)

# ================ АНАЛИЗ ВОДЫ ================
@dp.message_handler(Text(equals="🧪 Анализ воды"))
async def handle_analysis(message: types.Message):
    text = (
        "🧪 <b>Анализ воды</b>\n\n"
        "Анализ воды — первый и правильный шаг в подборе водоочистного оборудования.\n"
        "На основе химического и бактериологического анализа мы подберем оптимальное решение.\n\n"
        "⏱ <b>Срок:</b> 2–5 рабочих дней\n"
        "💰 <b>Стоимость:</b> 3500 руб.\n\n"
        "📍 <b>Как сдать:</b>\n"
        "ДНР, г. Донецк, ул. Щорса 38, магазин ДОНАКВА\n"
        "📞 +7 949 321‑98‑00\n\n"
        "📋 <b>Подготовка пробы:</b>\n"
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
        "🧪 <b>Химия:</b>\n"
        "• Дезинфекция (хлор, бром, активный кислород)\n"
        "• Регуляторы pH и щелочности\n"
        "• Альгициды (от водорослей)\n"
        "• Коагулянты и флокулянты\n"
        "• Средства для зимней консервации\n\n"
        "🔧 <b>Оборудование:</b>\n"
        "• Фильтры (песочные, картриджные)\n"
        "• Насосы и гидромассаж\n"
        "• Теплообменники и нагреватели\n"
        "• Автоматическая дозация\n"
        "• Аксессуары и комплекты запуска\n\n"
        "👇 <b>Выберите раздел:</b>"
    )
    await message.answer(text, reply_markup=pool_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🧪 Химия для бассейнов"))
async def handle_pool_chemistry(message: types.Message):
    text = (
        "🧪 <b>Химия для бассейнов</b>\n\n"
        "Опишите, какая химия вам нужна:\n\n"
        "• <b>Тип химии</b> (хлор, бром, альгицид, pH и т.д.)\n"
        "• <b>Объём бассейна</b> (в м³)\n"
        "• <b>Тип бассейна</b> (частный/общественный, каркасный/стационарный)\n"
        "• <b>Количество</b> (разовая покупка/регулярно)\n"
        "• <b>Проблема</b> (зелёная вода, мутная, запах)\n\n"
        "📌 <i>Пример: «Хлор в таблетках для бассейна 25 м³, зелёная вода»</i>\n\n"
        "Напишите одним сообщением — мы подберем дозировку!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🔧 Оборудование для бассейна"))
async def handle_pool_equipment(message: types.Message):
    text = (
        "🔧 <b>Оборудование для бассейна</b>\n\n"
        "Опишите, что нужно:\n\n"
        "• <b>Тип оборудования</b> (фильтр, насос, нагреватель, лестница)\n"
        "• <b>Объём бассейна</b> (в м³)\n"
        "• <b>Задача</b> (ремонт, замена, новый монтаж)\n"
        "• <b>Бренд</b> (есть предпочтения?)\n"
        "• <b>Бюджет</b> (эконом/стандарт/премиум)\n\n"
        "📌 <i>Пример: «Песочный фильтр для бассейна 35 м³, старый сломался»</i>\n\n"
        "Напишите одним сообщением — подберем совместимое оборудование!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🚀 Комплекты для запуска"))
async def handle_pool_startup(message: types.Message):
    text = (
        "🚀 <b>Комплекты для запуска бассейна</b>\n\n"
        "Опишите ваш бассейн:\n\n"
        "• <b>Объём</b> (в м³)\n"
        "• <b>Тип</b> (новый/после зимы/после ремонта)\n"
        "• <b>Фильтрация</b> (песочный/картриджный)\n"
        "• <b>Вода</b> (водопровод/скважина)\n\n"
        "📌 <i>Пример: «Запуск бассейна 45 м³, песочный фильтр, вода из скважины»</i>\n\n"
        "Напишите — соберем идеальный стартовый набор!"
    )
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message_handler(Text(equals="🎯 Подбор под мой бассейн"))
async def handle_pool_custom(message: types.Message):
    text = (
        "🎯 <b>Индивидуальный подбор</b>\n\n"
        "Опишите вашу ситуацию:\n\n"
        "• <b>Объём бассейна</b> (м³)\n"
        "• <b>Тип</b> (частный/общественный, бетонный/каркасный)\n"
        "• <b>Задача</b> (первичный подбор/замена/модернизация)\n"
        "• <b>Что нужно</b> (химия/оборудование/всё вместе)\n"
        "• <b>Бюджет и сроки</b>\n\n"
        "📌 <i>Пример: «Бассейн 60 м³, частный, бетонный. Нужен насос и дозация хлора. Бюджет до 150 000 руб.»</i>\n\n"
        "Напишите — подготовим КП в течение 24 часов!"
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
        "🔧 <b>Направления:</b>\n"
        "• Промышленные системы водоподготовки\n"
        "• Коммерческие системы очистки\n"
        "• Бытовые фильтры и системы\n\n"
        "🧪 <b>Анализ воды</b> — основа правильного подбора!\n\n"
        "📍 <b>Адрес:</b> г. Донецк, ул. Щорса, д. 38\n"
        "📞 <b>Телефон:</b> +7 949 321‑98‑00\n"
        "🌐 <b>Сайт:</b> www.donaqua.pro"
    )
    
    success = await send_logo(message.chat.id, text, site_kb, "HTML")
    if not success:
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
        "• Бурильщики скважин\n"
        "• Управляющие компании\n\n"
        "✅ <b>Что предлагаем:</b>\n"
        "• Выгодные условия\n"
        "• Техническая поддержка\n"
        "• Обучение\n"
        "• Маркетинговая поддержка\n\n"
        "Выберите вашу сферу:"
    )
    await message.answer(text, reply_markup=partner_kb, parse_mode="HTML")

@dp.message_handler(Text(equals=["Сантехник / монтажник", "Архитектор / дизайнер", "Прораб / строитель", "Бурильщик скважин", "Другое"]))
async def handle_partner_option(message: types.Message):
    role = message.text
    text = (
        f"✅ <b>Вы выбрали:</b> {role}\n\n"
        f"📋 Опишите:\n"
        f"• Чем занимаетесь\n"
        f"• Опыт работы\n"
        f"• Какой формат сотрудничества интересует\n\n"
        f"Мы свяжемся с вами для обсуждения!"
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
        "🌐 <b>Наш сайт:</b> www.donaqua.pro\n\n"
        "• Каталог оборудования\n"
        "• Цены и наличие\n"
        "• Наши работы\n"
        "• Контакты",
        reply_markup=back_kb,
        parse_mode="HTML"
    )

# ================ ФОТО ================
@dp.message_handler(content_types=ContentType.PHOTO)
async def handle_photo(message: types.Message):
    user = message.from_user
    user_info = f"{user.full_name} (@{user.username})"
    photo = message.photo[-1]
    
    try:
        await bot.send_photo(
            ADMIN_ID,
            photo.file_id,
            caption=f"📸 Новая заявка с фото\n👤 {user_info}\n💬 {message.caption or 'Без подписи'}"
        )
        await message.answer("✅ Спасибо! Заявка с фото отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        await message.answer("✅ Спасибо! Заявка получена.", reply_markup=main_kb)

# ================ ТЕКСТ ================
@dp.message_handler()
async def handle_text(message: types.Message):
    if message.text.startswith('/'):
        return
    
    user = message.from_user
    user_info = f"{user.full_name} (@{user.username}) id={user.id}"
    
    try:
        await bot.send_message(
            ADMIN_ID,
            f"📬 Новая заявка\n👤 {user_info}\n💬 {message.text}"
        )
        await message.answer("✅ Спасибо! Заявка отправлена.", reply_markup=main_kb)
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")
        await message.answer("✅ Спасибо! Заявка получена.", reply_markup=main_kb)

# ================ RENDER ================
from aiohttp import web

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
    print(f"🔑 Токен: {API_TOKEN[:10]}...")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print(f"🖼 Логотип: встроенный (base64)")
    
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
