import os
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

processed_messages = set()

# 🧠 تلخيص
def summarize(text):
    try:
        text = text[:3000]

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"لخص النص التالي في 3 نقاط قصيرة وواضحة:\n{text}"
        )

        return response.text

    except Exception as e:
        return f"❌ خطأ: {e}"

# 📌 التحقق من الرسالة المثبتة
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post

    if not message:
        return

    try:
        chat = await context.bot.get_chat(message.chat.id)

        # الحصول على آخر رسالة مثبتة
        pinned = chat.pinned_message

        if not pinned:
            return

        # إذا الرسالة الحالية هي المثبتة
        if message.message_id != pinned.message_id:
            return

        if message.message_id in processed_messages:
            return

        if not message.text:
            return

        if len(message.text.split()) < 75:
            return

        processed_messages.add(message.message_id)

        print("📌 تم اكتشاف رسالة مثبتة (بطريقة جديدة)")

        summary = summarize(message.text)

        # إرسال الرد (سيظهر في التعليقات)
        await context.bot.send_message(
            chat_id=message.chat.id,
            text=f"📌 التلخيص:\n\n{summary}",
            reply_to_message_id=message.message_id
        )

    except Exception as e:
        print(f"❌ Error: {e}")

# 🚀 تشغيل
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.CHANNEL, handle_channel_post)
    )

    print("✅ Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
