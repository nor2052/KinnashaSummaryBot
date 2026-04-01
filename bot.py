import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 📡 تخزين القنوات لكل مجموعة
group_channels = {}

# 🔒 قناة الاشتراك الإجباري (بدون @)
REQUIRED_CHANNEL = "nst3li8"

# ✅ التحقق من الاشتراك
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=f"@{REQUIRED_CHANNEL}",
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print("SUB ERROR:", e)
        return False

# 🧠 التلخيص عبر OpenRouter
def summarize(text):
    models = [
        "qwen/qwen3.6-plus-preview:free",
        "meta-llama/llama-3-8b-instruct:free"
    ]

    prompt = f"""
لخص النص التالي:

- اجعله في نقاط واضحة
- كل نقطة تبدأ بعنوان بالخط العريض
- ضع سطر فارغ بين كل نقطة
- اجعل النص سهل القراءة

النص:
{text}
"""

    for model in models:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5
                }
            )

            data = response.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            print("API ERROR:", e)
            continue

    return "❌ فشل التلخيص"

# 🚀 /start (مع أزرار)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{REQUIRED_CHANNEL}")],
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 مرحبًا!\n\n🔒 يجب الاشتراك أولاً لاستخدام البوت",
        reply_markup=reply_markup
    )

# 🔘 زر التحقق
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if await is_subscribed(user_id, context):
        await query.edit_message_text(
            "✅ تم التحقق من الاشتراك!\n\n"
            "📌 الخطوات التالية:\n"
            "1. أضفني إلى مجموعة\n"
            "2. اجعلني مشرفًا\n"
            "3. أرسل يوزر القناة داخل المجموعة مثل:\n"
            "@example"
        )
    else:
        await query.answer("❌ لم تشترك بعد!", show_alert=True)

# 📥 استقبال يوزر القناة داخل المجموعة
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.startswith("@"):
        return

    if update.message.chat.type == "private":
        await update.message.reply_text("❌ أرسل هذا داخل المجموعة")
        return

    group_id = update.message.chat_id
    username = update.message.text.replace("@", "")

    group_channels[group_id] = username

    await update.message.reply_text(
        f"✅ تم تفعيل التلخيص لهذه المجموعة\n📡 القناة: @{username}"
    )

# 📡 مراقبة الرسائل القادمة من القناة
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.sender_chat:
        return

    group_id = message.chat_id

    if group_id not in group_channels:
        return

    channel_username = group_channels[group_id]

    if message.sender_chat.username != channel_username:
        return

    if not message.text:
        return

    if len(message.text.split()) < 50:
        return

    summary = summarize(message.text)

    reply = f"""
<b>قَالَ المُحَشِّي الفَاضِل:</b>

{summary}

━━━━━━━━━━━

🚀 جرّب البوت الآن في مجموعتك
"""

    await message.reply_text(reply, parse_mode="HTML")

# 🚀 تشغيل البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))

    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, set_channel))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_messages))

    print("✅ Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
