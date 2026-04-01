import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

group_channels = {}
processed_messages = set()

# =============================
# 🧠 التلخيص
# =============================
def summarize(text):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen3.6-plus-preview:free",
                "messages": [
                    {
                        "role": "user",
                        "content": f"""لخص النص التالي في نقاط واضحة:

{text}
"""
                    }
                ]
            }
        )

        data = response.json()
        print("📊 API RESPONSE:", data)

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("❌ API ERROR:", e)

    return "❌ فشل التلخيص"

# =============================
# 👋 /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 مرحبًا بك في بوت التلخيص!\n\n"
        "📌 طريقة الاستخدام:\n"
        "1️⃣ أضف البوت إلى مجموعة\n"
        "2️⃣ أرسل منشور من القناة داخل المجموعة\n\n"
        "✅ سيتم ربط القناة تلقائيًا\n"
        "✍️ بعدها سيتم تلخيص أي منشور طويل\n\n"
        "🔧 أوامر:\n"
        "/unlink - فك ارتباط القناة"
    )

# =============================
# 🔓 /unlink
# =============================
async def unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id

    if group_id in group_channels:
        del group_channels[group_id]

        await update.message.reply_text(
            "🔓 تم فك ارتباط القناة بنجاح\n"
            "📌 يمكنك الآن ربط قناة جديدة"
        )
    else:
        await update.message.reply_text(
            "❌ لا توجد قناة مرتبطة بالفعل"
        )

# =============================
# 📥 استقبال الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔥 UPDATE RECEIVED")

    message = update.message
    if not message:
        print("❌ لا يوجد message")
        return

    group_id = message.chat_id

    print("TEXT:", message.text)
    print("SENDER_CHAT:", message.sender_chat)
    print("FORWARD:", message.forward_from_chat)

    # =============================
    # 📌 تسجيل القناة
    # =============================
    if message.sender_chat and message.sender_chat.type == "channel":
        if group_id not in group_channels:
            group_channels[group_id] = message.sender_chat.id

            await message.reply_text(
                f"✅ تم ربط القناة:\n{message.sender_chat.title}"
            )

            print("✅ تم تسجيل القناة")

    # =============================
    # ❗ لا توجد قناة
    # =============================
    if group_id not in group_channels:
        if message.text and not message.text.startswith("/"):
            await message.reply_text(
                "⚠️ لم يتم ربط قناة بعد\n"
                "📌 أرسل منشور من قناة لبدء الاستخدام"
            )
        return

    target_channel_id = group_channels[group_id]
    detected_channel_id = None

    # قناة مباشرة
    if message.sender_chat and message.sender_chat.type == "channel":
        detected_channel_id = message.sender_chat.id

    # forward
    elif message.forward_from_chat:
        detected_channel_id = message.forward_from_chat.id

    if not detected_channel_id:
        return

    if detected_channel_id != target_channel_id:
        return

    if message.message_id in processed_messages:
        return

    if not message.text:
        return

    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    print("✅ تم التقاط الرسالة!")

    summary = summarize(message.text)

    await message.reply_text(f"📌 التلخيص:\n\n{summary}")

# =============================
# 🚀 تشغيل
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("unlink", unlink))
    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    print("✅ Bot is running...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
