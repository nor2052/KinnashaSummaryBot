import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 🔑 ضع مفتاح Gemini هنا أو عبر Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)

# 🔁 منع تكرار معالجة نفس الرسالة
processed_messages = set()

# 🧠 دالة التلخيص
def summarize(text):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        # تقليم النص إذا كان طويل جدًا
        text = text[:3000]

        response = model.generate_content(
            f"لخص النص التالي في 3 نقاط قصيرة وواضحة:\n{text}"
        )

        return response.text

    except Exception as e:
        return f"❌ خطأ في التلخيص: {e}"

# 📌 عند تثبيت رسالة
async def handle_pinned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message and message.pinned_message:
        original = message.pinned_message

        # تجاهل إذا لا يوجد نص
        if not original.text:
            return

        # منع التكرار
        if original.message_id in processed_messages:
            return

        text = original.text

        # شرط عدد الكلمات
        if len(text.split()) < 75:
            return

        processed_messages.add(original.message_id)

        # التلخيص
        summary = summarize(text)

        # الرد
        await message.reply_text(f"📌 التلخيص:\n\n{summary}")

# 🚀 تشغيل البوت
def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, handle_pinned)
    )

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
