from enums import GenerationStatus

# --- Start & User Agreement ---
WELCOME_FIRST = (
    "✨ <b>Добро пожаловать!</b>\n\n"
    "Здесь ваши фотографии <b>оживают</b> — за считанные секунды "
    "любой снимок превратится в потрясающее видео.\n\n"
    "🎬 Улыбка, поворот головы, танец — выберите эффект, "
    "загрузите фото и получите результат!\n\n"
    "Для начала примите Пользовательское соглашение 👇"
)

WELCOME_MAIN = (
    "🎬 <b>Главное меню</b>\n\n"
    "Оживите любое фото за пару кликов.\n\n"
    "🎁 Получите 1 бесплатную генерацию за приглашение друга!\n"
    "Нажмите «Мой профиль» для подробностей"
)

AGREEMENT_ACCEPED = (
    "✅ Соглашение принято!\n\n"
    "Теперь все возможности бота доступны для вас. "
    "Нажмите кнопку ниже, чтобы начать 🚀"
)

# --- Buttons ---
BTN_AGREEMENT = "📖 Читать соглашение"
BTN_ACCEPT_AGREEMENT = "✅ Принять"
BTN_REVIVE_PHOTO = "🎬 Оживить фото"
BTN_POSTCARDS = "🎉 Открытки"
BTN_CUSTOM_PROMPT_MAIN = "✨ Создать свой сценарий"
BTN_PACKS = "📦 Наборы"
BTN_PROFILE = "👤 Мой профиль"
BTN_HELP = "❓ Помощь"
BTN_SETTINGS = "⚙️ Настройки"
BTN_DASHBOARD = "📊 Дашборд"
BTN_BACK = "🔙 Назад"
BTN_BUY_PACK = "{name} — {price_line} ({count} шт.)"
BTN_MOCK_PAY = "✅ Оплатить (Тест)"
BTN_LAVA_PAY = "💳 Оплатить через Lava"
BTN_PAY_OPEN_LINK = "🔗 Открыть оплату"
BTN_PAY_SKIP_EMAIL = "⏭ Пропустить email"
BTN_SKIP = "⏭ Пропустить"
BTN_CONFIRM = "✅ Подтвердить"
BTN_CUSTOM_PROMPT = "✨ Придумать свой"

# --- Postcards ---
POSTCARD_LIST = (
    "🎉 <b>Открытки</b>\n\n"
    "Выберите поздравительный шаблон — оживите фото \n"
    "и отправьте уникальную видео-открытку близким! 💌"
)
POSTCARD_EMPTY = "😔 Открытки временно недоступны. Заходите позже!"

# --- Help ---
HELP_TEXT = (
    "❓ <b>Помощь</b>\n\n"
    "По всем вопросам пишите в саппорт — @SpacePilgrim"
)

# --- Profile ---
PROFILE_TEXT = (
    "👤 <b>Ваш профиль</b>\n\n"
    "🆔 ID: <code>{user_id}</code>\n"
    "🎥 Генераций на балансе: <b>{balance}</b>\n\n"
    "🎁 <b>Получите бесплатную генерацию!</b>\n"
    "Ваш друг должен запустить бота по вашей ссылке ниже\n\n"
    "🔗 <b>Ваша реферальная ссылка:</b>\n"
    "<code>{ref_link}</code>\n\n"
    "👥 Приглашено друзей: <b>{ref_count}</b>\n"
    "💎 <i>За приглашение друга — бесплатная генерация</i>"
)

SETTINGS_TEXT = (
    "⚙️ <b>Настройки безопасности</b>\n\n"
    "🆔 Telegram ID: <code>{user_id}</code>\n"
    "👤 Telegram: {telegram_username}\n"
    "🔐 Логин админки: <code>{admin_login}</code>\n"
    "🛡 2FA: <b>{twofa_status}</b>\n\n"
    "Выберите действие ниже."
)
SETTINGS_TWOFA_ON = "включена"
SETTINGS_TWOFA_OFF = "выключена"
BTN_CHANGE_PASSWORD = "🔑 Сменить пароль"
BTN_TOGGLE_2FA_ON = "🛡 Включить 2FA"
BTN_TOGGLE_2FA_OFF = "🛡 Выключить 2FA"
BTN_SETTINGS_REFRESH = "🔄 Обновить"
SETTINGS_ENTER_CURRENT_PASSWORD = "Введите текущий пароль:"
SETTINGS_ENTER_NEW_PASSWORD = "Введите новый пароль:"
SETTINGS_PASSWORD_CHANGED = "✅ Пароль обновлен."
SETTINGS_PASSWORD_INVALID = "❌ Текущий пароль неверный."
SETTINGS_PASSWORD_TOO_SHORT = "❌ Новый пароль слишком короткий."
SETTINGS_CREDENTIALS_REQUIRED = "❌ Сначала задайте логин/пароль в веб-панели."
SETTINGS_2FA_UPDATED = "✅ Настройка 2FA обновлена."

# --- Templates ---
TEMPLATE_LIST = (
    "🎬 <b>Выберите стиль оживления</b>\n\n"
    "Каждый шаблон — уникальный эффект.\n"
    "Нажмите, чтобы посмотреть превью:"
)
TEMPLATE_EMPTY = "😔 Шаблоны временно недоступны. Заходите позже!"

def template_preview(name: str, has_balance: bool) -> str:
    text = f"🎬 <b>{name}</b>\n\n"
    if has_balance:
        text += (
            "У вас есть генерации на балансе! ✨\n"
            "Нажмите <b>«Подтвердить»</b>, чтобы начать магию."
        )
    else:
        text += (
            "💫 Хотите попробовать этот эффект?\n\n"
            "Приобретите набор генераций — это быстро и выгодно!"
        )
    return text

# --- Generation Flow ---
ASK_PHOTO = (
    "📸 <b>Отправьте фотографию</b>\n\n"
    "Загрузите фото лица крупным планом для лучшего результата.\n"
    "<i>Совет: хорошее освещение = потрясающее видео!</i>"
)
ASK_WISHES = (
    "📝 <b>Есть пожелания?</b>\n\n"
    "Опишите, что хотите увидеть на видео, "
    "или нажмите <b>«Пропустить»</b> — подберём за вас 😉"
)
ASK_CUSTOM_PROMPT = (
    "✍️ <b>Придумайте свой сценарий</b>\n\n"
    "Опишите всё, что хотите увидеть — "
    "ваш текст отправится в систему как есть.\n"
    "Или нажмите <b>«Пропустить»</b> для стандартного варианта."
)
PROMPT_ACCEPTED = "✅ Сценарий принят"
GENERATION_STARTED = (
    "⏳ <b>Фото отправлено на обработку!</b>\n\n"
    "Создаём ваше видео — результат придёт сюда "
    "обычно в течение пары минут ✨"
)
GENERATION_QUEUED = "⏳ В очереди..."
GENERATION_PROGRESS = "🔄 Обработка... {percent}%"
GENERATION_PROGRESS_NO_PERCENT = "🔄 Создаём ваше видео... Обычно это занимает около 90 секунд."
GENERATION_DRAFT_COMPLETED = "✅ Готово! Видео отправляется..."
GENERATION_VIDEO_READY = "✅ Ваше видео готово!"
GENERATION_DRAFT_STARTED = "🔄 Обработка... 0%"
GENERATION_START_ERROR = "❌ Ошибка при запуске генерации: {error}"
GENERATION_FAILED_ERROR = "❌ Ошибка при генерации:\n{error}"
GENERATION_TIMEOUT_ERROR = "❌ Время ожидания генерации истекло."
GENERATION_DIRECT_SEND_FAILED = "✅ Видео сгенерировано, но не удалось его отправить напрямую. Ссылка: {url}"
INSUFFICIENT_BALANCE = (
    "😔 <b>Генерации закончились</b>\n\n"
    "Пополните баланс, чтобы продолжить создавать потрясающие видео!"
)
INSUFFICIENT_BALANCE_ALERT = "😔 Генерации закончились. Пополните баланс!"
GENERATION_ALREADY_IN_PROGRESS = (
    "⏳ У вас уже идёт генерация.\n\n"
    "Дождитесь завершения текущей, затем запустите новую."
)
GENERATION_ALREADY_IN_PROGRESS_ALERT = "У вас уже идёт генерация, дождитесь завершения."

# --- Packs ---
PACKS_LIST = (
    "📦 <b>Наборы генераций</b>\n\n"
    "Выберите подходящий набор и оживляйте фото без ограничений!\n"
    "💡 <i>Чем больше набор — тем выгоднее цена за генерацию.</i>"
)
PACKS_EMPTY = "😔 Наборы временно недоступны."
PACK_DETAILS = (
    "📦 <b>{name}</b>\n\n"
    "{description}\n\n"
    "🎥 Генераций: <b>{count}</b>\n"
    "💰 Цена: <b>{price_line}</b>\n"
    "📊 <i>Всего {per_gen_line} за генерацию</i>"
)

PAYMENT_SUCCESS = (
    "🎉 <b>Оплата прошла успешно!</b>\n\n"
    "Генерации уже на вашем балансе. "
    "Скорее оживляйте фото! 🚀"
)
PAYMENT_ENTER_EMAIL = (
    "📧 <b>Укажите email для оплаты</b>\n\n"
    "На этот email придет чек от платежной системы.\n"
    "Можно пропустить, но тогда чек не будет доставлен."
)
PAYMENT_INVALID_EMAIL = "❌ Неверный формат email. Попробуйте еще раз."
PAYMENT_EMAIL_SKIPPED_WARNING = "⚠️ Вы пропустили email. Для оплаты будет использован технический адрес."
PAYMENT_CREATED_OPEN_LINK = (
    "💳 Ссылка на оплату сформирована.\n\n"
    "Нажмите кнопку ниже и завершите оплату.\n"
    "После подтверждения генерации начислятся автоматически."
)
PAYMENT_PROVIDER_UNAVAILABLE = "❌ Платежный провайдер временно недоступен."
PAYMENT_OFFER_NOT_CONFIGURED = "❌ Для этого пакета не задан offerId Lava.top."
PAYMENT_CONFIRMED_NOTIFY = "✅ Оплата подтверждена! Вам начислено <b>{count}</b> генераций."

# --- Referrals ---
REFERRAL_APPLIED = "🎉 Вы зарегистрировались по реферальной ссылке! Бонус начислен."
NEW_REFERRAL_BONUS = "🎉 По вашей ссылке пришёл новый пользователь! Вам начислена <b>1 бесплатная генерация</b>."

# --- Errors ---
ERROR_GENERIC = "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
ERROR_NOT_PHOTO = "❌ Пожалуйста, отправьте именно фотографию (не файл, не документ)."

# --- Dashboard ---
DASHBOARD_TITLE = "Дашборд"
DASHBOARD_USERS = "Пользователи"
DASHBOARD_GENERATIONS = "Генерации"
DASHBOARD_REVENUE = "Выручка за месяц"
DASHBOARD_TODAY = "Сегодня"
DASHBOARD_PERFORMANCE = "Производительность"
DASHBOARD_AVG_TIME = "Среднее время"
DASHBOARD_STATUS = "Статус"
DASHBOARD_TOP_TEMPLATES = "Топ шаблоны"
DASHBOARD_BALANCE = "Баланс"
DASHBOARD_CREDITS = "кредиты"
DASHBOARD_REMAINING = "Осталось генераций"
DASHBOARD_MODEL = "Модель"
DASHBOARD_PIAPI_UNAVAILABLE = "PiAPI недоступен"
DASHBOARD_METRICS_UNAVAILABLE = "Метрики недоступны"
BTN_DASHBOARD_REFRESH = "🔄 Обновить"
BTN_DASHBOARD_BACK = "🔙 Назад"

STATUS_MESSAGES = {
    GenerationStatus.PENDING: "⏳ В очереди...",
    GenerationStatus.PROCESSING: "🔄 Создаём видео...",
    GenerationStatus.COMPLETED: "✅ Ваше видео готово!",
    GenerationStatus.FAILED: "❌ Ошибка при генерации.",
}
