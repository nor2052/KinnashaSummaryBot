import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 📡 تخزين القنوات لكل مجموعة
group_channels = {}

processed_messages = set()

# =============================
# 🧠 التلخيص
# =============================
def summarize(text):
    model = "qwen/qwen3.6-plus-preview:free"

    try:
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
# 📌 تسجيل القناة تلقائيًا
# =============================
async def register_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    # 🔍 تشخيص
    print("🟡 REGISTER CHECK")
    print("sender_chat:", message.sender_chat)

    if not message.sender_chat:
        return

    group_id = message.chat_id

    if group_id not in group_channels:
        group_channels[group_id] = message.sender_chat.id

        print("✅ تم تسجيل القناة:")
        print("NAME:", message.sender_chat.title)
        print("ID:", message.sender_chat.id)

# =============================
# 📥 التقاط الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    print("\n📩 ===== NEW UPDATE =====")

    if not message:
        print("❌ لا يوجد message")
        return

    print("TEXT:", message.text)
    print("CHAT TYPE:", message.chat.type)
    print("SENDER_CHAT:", message.sender_chat)
    print("FORWARD_FROM_CHAT:", message.forward_from_chat)

    group_id = message.chat_id

    if group_id not in group_channels:
        print("❌ هذه المجموعة غير مسجلة")
        return

    target_channel_id = group_channels[group_id]
    detected_channel_id = None

    # حالة 1: رسالة مباشرة من قناة
    if message.sender_chat:
        detected_channel_id = message.sender_chat.id

    # حالة 2: forward من قناة
    elif message.forward_from_chat:
        detected_channel_id = message.forward_from_chat.id

    if not detected_channel_id:
        print("❌ لم يتم التعرف على القناة")
        return

    print("📡 Detected Channel ID:", detected_channel_id)
    print("🎯 Target Channel ID:", target_channel_id)

    if detected_channel_id != target_channel_id:
        print("❌ القناة لا تطابق")
        return

    if message.message_id in processed_messages:
        print("⚠️ رسالة مكررة")
        return

    if not message.text:
        print("❌ لا يوجد نص")
        return

    if len(message.text.split()) < 75:
        print("❌ النص قصير")
        return

    processed_messages.add(message.message_id)

    print("✅ تم التقاط الرسالة بنجاح!")

    summary = summarize(message.text)

    await message.reply_text(f"📌 التلخيص:\n\n{summary}")

# =============================
# 🚀 تشغيل
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 🔥 أهم شيء: ALL وليس TEXT
    app.add_handler(MessageHandler(filters.ALL, register_channel))
    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    print("✅ Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
