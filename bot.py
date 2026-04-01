import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 🔑 ضع المفاتيح هنا
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = "PUT_YOUR_OPENROUTER_API_KEY_HERE"

# اسم القناة بدون @
CHANNEL_USERNAME = "Kinnasha"

processed_messages = set()

# 🧠 دالة التلخيص باستخدام OpenRouter
def summarize(text):
    try:
        text = text[:3000]

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
لخص النص التالي:
- في 3 نقاط
- بأسلوب واضح ومختصر

النص:
{text}
"""
                    }
                ]
            }
        )

        data = response.json()

        # 🔍 اطبع الرد الكامل للتشخيص
        print("📊 API RESPONSE:", data)

        # ✅ تحقق قبل الاستخدام
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            return f"❌ خطأ من API:\n{data}"

    except Exception as e:
        return f"❌ خطأ: {e}"
# 📥 استقبال الرسائل
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    # لازم تكون الرسالة من قناة
    if not message.sender_chat:
        return

    # التأكد أنها من القناة المطلوبة
    if message.sender_chat.username != CHANNEL_USERNAME:
        return

    # منع التكرار
    if message.message_id in processed_messages:
        return

    # لازم تكون نص
    if not message.text:
        return

    # شرط عدد الكلمات
    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    print("📌 تم اكتشاف رسالة من القناة")

    summary = summarize(message.text)

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
