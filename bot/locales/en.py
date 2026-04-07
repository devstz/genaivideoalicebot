from enums import GenerationStatus

# --- Start & User Agreement ---
WELCOME_FIRST = (
    "✨ <b>Welcome!</b>\n\n"
    "Turn any photo into a stunning <b>AI-powered video</b> "
    "in just seconds.\n\n"
    "🎬 Smiles, head turns, dancing — pick an effect, "
    "upload a photo, and watch the magic happen!\n\n"
    "Please accept the User Agreement to get started 👇"
)

WELCOME_MAIN = (
    "🎬 <b>Main Menu</b>\n\n"
    "Bring any photo to life in just a few taps.\n\n"
    "🎁 Get 1 free generation by inviting a friend!\n"
    "Tap «My Profile» for details"
)

AGREEMENT_ACCEPED = (
    "✅ Agreement accepted!\n\n"
    "All features are now unlocked. "
    "Tap below to start creating 🚀"
)

# --- Buttons ---
BTN_AGREEMENT = "📖 Read Agreement"
BTN_ACCEPT_AGREEMENT = "✅ Accept"
BTN_REVIVE_PHOTO = "🎬 Animate Photo"
BTN_PACKS = "📦 Packs"
BTN_PROFILE = "👤 Profile"
BTN_BACK = "🔙 Back"
BTN_BUY_PACK = "{name} — {price_line} ({count} pcs)"
BTN_MOCK_PAY = "✅ Pay (Test)"
BTN_LAVA_PAY = "💳 Pay with Lava"
BTN_LAVA_PAY_SBP = "💳 Pay via SBP"
BTN_PAY_OPEN_LINK = "🔗 Open payment page"
BTN_PAY_SKIP_EMAIL = "⏭ Skip email"
BTN_SKIP = "⏭ Skip"
BTN_CONFIRM = "✅ Confirm"
BTN_CUSTOM_PROMPT = "✨ Create your own"
BTN_DASHBOARD = "📊 Dashboard"

# --- Profile ---
PROFILE_TEXT = (
    "👤 <b>Your Profile</b>\n\n"
    "🆔 ID: <code>{user_id}</code>\n"
    "🎥 Generations left: <b>{balance}</b>\n\n"
    "🎁 <b>Get a free generation!</b>\n"
    "Your friend needs to start the bot using your link below\n\n"
    "🔗 <b>Your referral link:</b>\n"
    "<code>{ref_link}</code>\n\n"
    "👥 Friends invited: <b>{ref_count}</b>\n"
    "💎 <i>Invite a friend — get a free generation</i>"
)

# --- Templates ---
TEMPLATE_LIST = (
    "🎬 <b>Choose an animation style</b>\n\n"
    "Each template is a unique effect.\n"
    "Tap to preview:"
)
TEMPLATE_EMPTY = "😔 No templates available right now. Check back later!"

def template_preview(name: str, has_balance: bool) -> str:
    text = f"🎬 <b>{name}</b>\n\n"
    if has_balance:
        text += (
            "You have generations on your balance! ✨\n"
            "Tap <b>«Confirm»</b> to start the magic."
        )
    else:
        text += (
            "💫 Want to try this effect?\n\n"
            "Grab a generation pack — it's quick and affordable!"
        )
    return text

# --- Generation Flow ---
ASK_PHOTO = (
    "📸 <b>Send a photo</b>\n\n"
    "Upload a close-up face photo for the best result.\n"
    "<i>Tip: good lighting = amazing video!</i>"
)
ASK_WISHES = (
    "📝 <b>Any special requests?</b>\n\n"
    "Describe what you'd like to see, "
    "or tap <b>«Skip»</b> — we'll pick for you 😉"
)
ASK_CUSTOM_PROMPT = (
    "✍️ <b>Create your own scenario</b>\n\n"
    "Describe everything you want to see — "
    "your text will be sent as is.\n"
    "Or tap <b>«Skip»</b> for a default option."
)
PROMPT_ACCEPTED = "✅ Prompt accepted"
GENERATION_STARTED = (
    "⏳ <b>Photo submitted!</b>\n\n"
    "Creating your video — the result will arrive here "
    "usually within a couple of minutes ✨"
)
GENERATION_QUEUED = "⏳ Queued..."
GENERATION_PROGRESS = "🔄 Processing... {percent}%"
GENERATION_PROGRESS_NO_PERCENT = "🔄 Creating your video... This usually takes about 90 seconds."
GENERATION_DRAFT_COMPLETED = "✅ Done! Sending video..."
GENERATION_VIDEO_READY = "✅ Your video is ready!"
GENERATION_DRAFT_STARTED = "🔄 Processing... 0%"
GENERATION_START_ERROR = "❌ Failed to start generation: {error}"
GENERATION_FAILED_ERROR = "❌ Generation failed:\n{error}"
GENERATION_TIMEOUT_ERROR = "❌ Generation timed out."
GENERATION_DIRECT_SEND_FAILED = "✅ The video is generated, but direct delivery failed. Link: {url}"
INSUFFICIENT_BALANCE = (
    "😔 <b>No generations left</b>\n\n"
    "Top up your balance to keep creating amazing videos!"
)
INSUFFICIENT_BALANCE_ALERT = "😔 No generations left. Top up your balance!"
GENERATION_ALREADY_IN_PROGRESS = (
    "⏳ You already have an active generation.\n\n"
    "Please wait for it to finish, then start a new one."
)
GENERATION_ALREADY_IN_PROGRESS_ALERT = "You already have an active generation. Please wait for it to finish."

# --- Packs ---
PACKS_LIST = (
    "📦 <b>Generation Packs</b>\n\n"
    "Pick a pack and animate photos without limits!\n"
    "💡 <i>Bigger packs = better price per generation.</i>"
)
PACKS_EMPTY = "😔 No packs available at the moment."
PACK_DETAILS = (
    "📦 <b>{name}</b>\n\n"
    "{description}\n\n"
    "🎥 Generations: <b>{count}</b>\n"
    "💰 Price: <b>{price_line}</b>\n"
    "📊 <i>Just {per_gen_line} per generation</i>"
)

PAYMENT_SUCCESS = (
    "🎉 <b>Payment successful!</b>\n\n"
    "Generations have been added to your balance. "
    "Start animating photos now! 🚀"
)
PAYMENT_ENTER_EMAIL = (
    "📧 <b>Enter your email for payment</b>\n\n"
    "The receipt from the payment system will be sent to this email.\n"
    "You can skip, but then no receipt will be delivered."
)
PAYMENT_INVALID_EMAIL = "❌ Invalid email format. Please try again."
PAYMENT_EMAIL_SKIPPED_WARNING = "⚠️ You skipped email. A technical address will be used for payment."
PAYMENT_CREATED_OPEN_LINK = (
    "💳 Payment link has been created.\n\n"
    "Open the link below and complete the payment.\n"
    "Generations will be credited automatically after confirmation."
)
PAYMENT_PROVIDER_UNAVAILABLE = "❌ Payment provider is temporarily unavailable."
PAYMENT_OFFER_NOT_CONFIGURED = "❌ This pack has no Lava.top offerId configured."
PAYMENT_CONFIRMED_NOTIFY = "✅ Payment confirmed! <b>{count}</b> generations were credited."

# --- Referrals ---
REFERRAL_APPLIED = "🎉 You signed up via a referral link! Bonus credited."
NEW_REFERRAL_BONUS = "🎉 A new user joined with your link! You've received <b>1 free generation</b>."

# --- Errors ---
ERROR_GENERIC = "❌ Something went wrong. Please try again later."
ERROR_NOT_PHOTO = "❌ Please send a photo (not a file or document)."

# --- Dashboard ---
DASHBOARD_TITLE = "Dashboard"
DASHBOARD_USERS = "Users"
DASHBOARD_GENERATIONS = "Generations"
DASHBOARD_REVENUE = "Revenue (month)"
DASHBOARD_TODAY = "Today"
DASHBOARD_PERFORMANCE = "Performance"
DASHBOARD_AVG_TIME = "Avg time"
DASHBOARD_STATUS = "Status"
DASHBOARD_TOP_TEMPLATES = "Top templates"
DASHBOARD_BALANCE = "Balance"
DASHBOARD_CREDITS = "credits"
DASHBOARD_REMAINING = "Remaining generations"
DASHBOARD_MODEL = "Model"
DASHBOARD_PIAPI_UNAVAILABLE = "PiAPI unavailable"
DASHBOARD_METRICS_UNAVAILABLE = "Metrics unavailable"
BTN_DASHBOARD_REFRESH = "🔄 Refresh"
BTN_DASHBOARD_BACK = "🔙 Back"

STATUS_MESSAGES = {
    GenerationStatus.PENDING: "⏳ Queued...",
    GenerationStatus.PROCESSING: "🔄 Creating video...",
    GenerationStatus.COMPLETED: "✅ Your video is ready!",
    GenerationStatus.FAILED: "❌ Generation failed.",
}
