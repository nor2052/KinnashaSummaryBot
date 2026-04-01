import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

# 🔑 مفاتيح
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 🔒 قناة الاشتراك الإجباري
REQUIRED_CHANNEL = "nst3li8"

# 📡 تخزين القنوات لكل مجموعة
group_channels = {}

processed_messages = set()

# =============================
# ✅ التحقق من الاشتراك
# =============================
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=f"@{REQUIRED_CHANNEL}",
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# =============================
# 🧠 التلخيص (كما هو عندك)
# =============================
def summarize(text):
    models = [
        "qwen/qwen3.6-plus-preview:free"
    ]

    text = text[:3000]

    for model in models:
        try:
            print(f"🔄 Trying model: {model}")

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""
لخص النص التالي:
- في نقاط واضحة
- بأسلوب بسيط

{text}
"""
                        }
                    ]
                }
            )

            data = response.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            print("ERROR:", e)
            continue

    return "❌ فشل التلخيص"

# =============================
# 🚀 /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{REQUIRED_CHANNEL}")],
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
    ]

    await update.message.reply_text(
        "🔒 يجب الاشتراك أولاً لاستخدام البوت",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# 🔘 تحقق الاشتراك
# =============================
async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_subscribed(query.from_user.id, context):
        await query.edit_message_text(
            "✅ تم التحقق\n\n"
            "📌 الآن:\n"
            "1. أضفني إلى مجموعة\n"
            "2. اجعلني مشرفًا\n"
            "3. أرسل يوزر القناة داخل المجموعة"
        )
    else:
        await query.answer("❌ لم تشترك بعد", show_alert=True)

# =============================
# 📥 تحديد القناة (مرة واحدة فقط)
# =============================
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    if message.chat.type == "private":
        return

    if not message.text.startswith("@"):
        return

    group_id = message.chat_id

    # ❗ إذا تم تحديد قناة مسبقًا → تجاهل
    if group_id in group_channels:
        return

    username = message.text.replace("@", "").lower()
    group_channels[group_id] = username

    print(f"✅ تم حفظ القناة: {username}")

# =============================
# 📡 التقاط رسائل القناة (كما كودك)
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    if not message.sender_chat:
        return

    group_id = message.chat_id

    # ❗ لازم تكون المجموعة مسجلة
    if group_id not in group_channels:
        return

    channel_username = group_channels[group_id]

    # ❗ التأكد من القناة
    if not message.sender_chat.username:
        return

    if message.sender_chat.username.lower() != channel_username:
        return

    # منع التكرار
    if message.message_id in processed_messages:
        return

    if not message.text:
        return

    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    print("📌 تم اكتشاف رسالة من القناة")

    summary = summarize(message.text)

    await message.reply_text(f"قَالَ المُحَشِّي الفَاضِل:\n\n{summary}")

# =============================
# 🚀 تشغيل
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_sub, pattern="check_sub"))

    # استقبال يوزر القناة
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, set_channel))

    # التقاط الرسائل
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_messages))

    print("✅ Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
