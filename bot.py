import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 📦 تخزين القنوات لكل مجموعة
group_channels = {}

# 🔒 قناة الاشتراك الإجباري
REQUIRED_CHANNEL = "yourchannel"  # بدون @

# ✅ التحقق من الاشتراك
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(f"@{REQUIRED_CHANNEL}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🧠 التلخيص
def summarize(text):
    models = [
        "qwen/qwen3.6-plus-preview:free",
        "meta-llama/llama-3-8b-instruct:free"
    ]

    prompt = f"""
لخص النص التالي في نقاط واضحة وقصيرة:

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

        except:
            continue

    return "❌ فشل التلخيص"

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(user_id, context):
        await update.message.reply_text(
            f"🚫 يجب الاشتراك أولاً في القناة:\n@{REQUIRED_CHANNEL}\n\nثم أعد إرسال /start"
        )
        return

    await update.message.reply_text(
        "👋 أهلاً بك!\n\n"
        "📌 الخطوات:\n"
        "1. أضفني إلى مجموعة\n"
        "2. اجعلني مشرفًا\n"
        "3. أرسل يوزر القناة هنا مثل:\n"
        "@example\n\n"
        "🚀 وسأقوم بالتلخيص تلقائيًا"
    )

# 📥 استقبال يوزر القناة
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

# 📥 مراقبة الرسائل
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

    # ✨ التنسيق المطلوب
    reply = f"""
<b>قَالَ المُحَشِّي الفَاضِل:</b>

{summary}
"""

    await message.reply_text(reply, parse_mode="HTML")

# 🚀 تشغيل
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, set_channel))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_messages))

    print("✅ Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
