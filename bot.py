import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 📡 كل مجموعة لها قناة (بالـ ID)
group_channels = {}

processed_messages = set()

# 🧠 التلخيص
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

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("ERROR:", e)

    return "❌ فشل التلخيص"


# 📌 تسجيل القناة (من أول رسالة)
async def register_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.sender_chat:
        return

    group_id = message.chat_id

    # إذا لم يتم تسجيل قناة بعد
    if group_id not in group_channels:
        group_channels[group_id] = message.sender_chat.id

        print("✅ تم تسجيل القناة:", message.sender_chat.title)
        print("ID:", message.sender_chat.id)


# 📥 التقاط الرسائل
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    print("📩 NEW MESSAGE")

    group_id = message.chat_id

    if group_id not in group_channels:
        return

    target_channel_id = group_channels[group_id]

    detected_channel_id = None

    # حالة قناة مباشرة
    if message.sender_chat:
        detected_channel_id = message.sender_chat.id

    # حالة forward
    elif message.forward_from_chat:
        detected_channel_id = message.forward_from_chat.id

    if not detected_channel_id:
        return

    print("📡 Detected ID:", detected_channel_id)

    if detected_channel_id != target_channel_id:
        return

    if message.message_id in processed_messages:
        return

    if not message.text:
        return

    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    print("📌 تم اكتشاف رسالة صحيحة!")

    summary = summarize(message.text)

    await message.reply_text(f"قَالَ المُحَشِّي الفَاضِل:\n\n{summary}")


# 🚀 تشغيل
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # تسجيل القناة تلقائيًا
    app.add_handler(MessageHandler(filters.ALL, register_channel))

    # التقاط الرسائل
    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    print("✅ Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
