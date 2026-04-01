import os
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 🔑 قراءة المفاتيح من Environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 🔁 منع التكرار
processed_messages = set()

# 🧠 دالة التلخيص (Gemini الجديد)
def summarize(text):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        text = text[:3000]

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"لخص النص التالي في 3 نقاط قصيرة وواضحة:\n{text}"
        )

        return response.text

    except Exception as e:
        return f"❌ خطأ في التلخيص: {e}"

# 📌 عند تثبيت رسالة
async def handle_pinned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message and message.pinned_message:
        original = message.pinned_message

        if not original.text:
            return

        if original.message_id in processed_messages:
            return

        text = original.text

        if len(text.split()) < 75:
            return

        processed_messages.add(original.message_id)

        print("📌 تم اكتشاف رسالة مثبتة")

        summary = summarize(text)

        await message.reply_text(f"📌 التلخيص:\n\n{summary}")

# 🚀 تشغيل البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, handle_pinned)
    )

    print("✅ Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()