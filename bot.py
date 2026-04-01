import os
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# اسم مستخدم القناة (مهم)
CHANNEL_USERNAME = "Kinnasha"

client = genai.Client(api_key=GEMINI_API_KEY)

processed_messages = set()

# 🧠 التلخيص
def summarize(text):
    models = [
        "gemini-2.0-flash",
        "gemini-1.5-pro"
    ]

    text = text[:3000]

    for model_name in models:
        try:
            print(f"🔄 Trying model: {model_name}")

            response = client.models.generate_content(
                model=model_name,
                contents=[{
                    "role": "user",
                    "parts": [f"لخص النص التالي في 3 نقاط قصيرة:\n{text}"]
                }]
            )

            print(f"✅ Success with: {model_name}")
            return response.candidates[0].content.parts[0].text

        except Exception as e:
            print(f"❌ Failed with {model_name}: {e}")
            continue

    return "❌ فشل الاتصال بـ Gemini API"
# 📥 استقبال الرسائل في المجموعة
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    # التحقق أن الرسالة من قناة
    if not message.sender_chat:
        return

    # التأكد أنها من قناتك فقط
    if message.sender_chat.username != CHANNEL_USERNAME:
        return

    # منع التكرار
    if message.message_id in processed_messages:
        return

    # يجب أن تكون نص
    if not message.text:
        return

    # شرط الطول
    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    print("📌 تم اكتشاف رسالة من القناة")

    summary = summarize(message.text)

    # الرد على نفس الرسالة
    await message.reply_text(f"📌 التلخيص:\n\n{summary}")

# 🚀 تشغيل البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_messages)
    )

    print("✅ Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
