import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

REQUIRED_CHANNEL = "nst3li8"

# user_id -> set of channels
user_channels = {}
processed_messages = set()

# 🧠 التلخيص
def summarize(text):
    models = [
        "qwen/qwen3.6-plus-preview:free",
        "bytedance/seedance-1-5-pro"
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
- في نقاط
- مختصر وواضح

{text}
"""
                        }
                    ]
                }
            )

            data = response.json()
            print("📊 RESPONSE:", data)

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            print("❌ Summarize error:", e)

    return "❌ فشل التلخيص"

# ✅ التحقق من الاشتراك
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=f"@{REQUIRED_CHANNEL}",
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]

    except Exception as e:
        print("❌ Subscription check error:", e)
        return False

# 🚀 بدء الاستخدام
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    print(f"👤 New user: {user_id}")

    if not await is_subscribed(user_id, context):
        await update.message.reply_text(
            f"❌ يجب الاشتراك في القناة أولاً:\nhttps://t.me/{REQUIRED_CHANNEL}"
        )
        return

    await update.message.reply_text(
        "✅ تم التحقق من الاشتراك\n\n"
        "📌 الآن:\n"
        "1- أضف البوت كمشرف في مجموعة القناة\n"
        "2- أرسل يوزر القناة (مثال: @channel)"
    )

# 📌 تسجيل القناة
async def register_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not text.startswith("@"):
        return

    channel_username = text.replace("@", "")

    try:
        chat = await context.bot.get_chat(f"@{channel_username}")
        print(f"📡 Found channel: {channel_username}")

        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)

        if bot_member.status not in ["administrator", "creator"]:
            await update.message.reply_text("❌ يجب جعل البوت مشرف أولاً")
            return

        if user_id not in user_channels:
            user_channels[user_id] = set()

        if channel_username in user_channels[user_id]:
            print("⚠️ Channel already registered")
            return

        user_channels[user_id].add(channel_username)

        await update.message.reply_text(
            f"✅ تم ربط القناة: @{channel_username}"
        )

    except Exception as e:
        print("❌ Channel error:", e)
        await update.message.reply_text("❌ لم أستطع الوصول للقناة")

# 📥 استقبال الرسائل
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.sender_chat:
        return

    channel_username = message.sender_chat.username

    # ✅ تحقق أن القناة مسجلة
    found = any(
        channel_username in channels
        for channels in user_channels.values()
    )

    if not found:
        return

    # منع التكرار
    if message.message_id in processed_messages:
        return

    if not message.text:
        return

    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    print(f"📌 Message from channel: {channel_username}")

    summary = summarize(message.text)

    try:
        await message.reply_text(f"📜 التلخيص:\n\n{summary}")
    except Exception as e:
        print("❌ Reply error:", e)

# 🚀 تشغيل البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, register_channel))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_messages))

    print("✅ Bot running...")

    app.run_polling()

if __name__ == "__main__":
    main()
