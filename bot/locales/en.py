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
    "Bring any photo to life in just a few taps.\n"
    "Choose an action:"
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
BTN_BUY_PACK = "{name} — {price} RUB ({count} pcs)"
BTN_MOCK_PAY = "✅ Pay (Test)"
BTN_SKIP = "⏭ Skip"
BTN_CONFIRM = "✅ Confirm"
BTN_CUSTOM_PROMPT = "✍️ Custom prompt"

# --- Profile ---
PROFILE_TEXT = (
    "👤 <b>Your Profile</b>\n\n"
    "🆔 ID: <code>{user_id}</code>\n"
    "🎥 Generations left: <b>{balance}</b>\n\n"
    "🔗 <b>Your referral link:</b>\n"
    "<code>{ref_link}</code>\n\n"
    "👥 Friends invited: <b>{ref_count}</b>\n"
    "💎 <i>Each friend = 1 free generation for you!</i>"
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
    "or tap <b>«Skip»</b> — our AI knows what to do 😉"
)
ASK_CUSTOM_PROMPT = (
    "✍️ <b>Enter full prompt</b>\n\n"
    "Describe everything you want to see in the video — "
    "this text will be sent to the AI as-is.\n"
    "Or tap <b>«Skip»</b> for a default scenario."
)
GENERATION_STARTED = (
    "⏳ <b>Photo submitted!</b>\n\n"
    "Our AI is working its magic on your video. "
    "The result will arrive in this chat — usually takes a couple of minutes ✨"
)
GENERATION_QUEUED = "⏳ Queued..."
GENERATION_PROGRESS = "🔄 Processing... {percent}%"
GENERATION_PROGRESS_NO_PERCENT = "🔄 AI is processing your video..."
GENERATION_DRAFT_COMPLETED = "✅ Done! Sending video..."
INSUFFICIENT_BALANCE = (
    "😔 <b>No generations left</b>\n\n"
    "Top up your balance to keep creating amazing videos!"
)

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
    "💰 Price: <b>{price} RUB</b>\n"
    "📊 <i>Just {per_gen} RUB per generation</i>"
)

PAYMENT_SUCCESS = (
    "🎉 <b>Payment successful!</b>\n\n"
    "Generations have been added to your balance. "
    "Start animating photos now! 🚀"
)

# --- Referrals ---
REFERRAL_APPLIED = "🎉 You signed up via a referral link! Bonus credited."
NEW_REFERRAL_BONUS = "🎉 A new user joined with your link! You've received <b>1 free generation</b>."

# --- Errors ---
ERROR_GENERIC = "❌ Something went wrong. Please try again later."
ERROR_NOT_PHOTO = "❌ Please send a photo (not a file or document)."

STATUS_MESSAGES = {
    GenerationStatus.PENDING: "⏳ Queued...",
    GenerationStatus.PROCESSING: "🔄 AI is processing...",
    GenerationStatus.COMPLETED: "✅ Your video is ready!",
    GenerationStatus.FAILED: "❌ Generation failed.",
}
