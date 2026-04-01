import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

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
                        "content": f"لخص النص التالي في نقاط واضحة:\n{text}"
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
# 📥 استقبال الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔥 UPDATE RECEIVED")

    message = update.message
    if not message:
        print("❌ لا يوجد message")
        return

    group_id = message.chat_id

    # 🔍 عرض كل شيء للتشخيص
    print("TEXT:", message.text)
    print("SENDER_CHAT:", message.sender_chat)
    print("FORWARD:", message.forward_from_chat)

    # =============================
    # 📌 تسجيل القناة (مرة واحدة)
    # =============================
    if message.sender_chat and message.sender_chat.type == "channel":
        if group_id not in group_channels:
            group_channels[group_id] = message.sender_chat.id
            print("✅ تم تسجيل القناة:", message.sender_chat.title)

    # =============================
    # ❗ إذا لم تسجل قناة → خروج
    # =============================
    if group_id not in group_channels:
        print("❌ لا توجد قناة مسجلة")
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
        print("❌ ليست رسالة قناة")
        return

    print("📡 Detected:", detected_channel_id)
    print("🎯 Target:", target_channel_id)

    if detected_channel_id != target_channel_id:
        print("❌ قناة مختلفة")
        return

    if message.message_id in processed_messages:
        return

    if not message.text:
        print("❌ لا يوجد نص")
        return

    if len(message.text.split()) < 75:
        print("❌ النص قصير")
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

    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    print("✅ Bot is running...")

    # 🔥 هذا هو الحل الحقيقي
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
