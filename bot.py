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
                        "content": f"لخص النص التالي:
- في عدد نقاط مناسب
- بأسلوب واضح ومختصر
وقم بكتابة النص بطريقة مقروءة وضع مسافات بين النقاط واجعل النصر اختصارًا للنص الأصلي ولا تكتب أي شيء قبل الملخص فقط أرسل الملخص وحسب دون أن تبين أنك ترد على أحد جاعلًا منه نصًا موضوعيًا:\n{text}"
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
# 🚀 رسالة البداية
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\n\n"
        "📌 طريقة الاستخدام:\n\n"
        "1️⃣ أضف البوت إلى مجموعة\n"
        "2️⃣ اجعله مشرف\n"
        "3️⃣ أرسل منشور من القناة داخل المجموعة\n\n"
        "✅ سيقوم البوت تلقائيًا بالتعرف على القناة وربطها\n"
        "✍️ بعدها أي منشور طويل سيتم تلخيصه تلقائيًا"
    )

# =============================
# 📥 استقبال الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔥 UPDATE RECEIVED")

    message = update.message
    if not message:
        return

    group_id = message.chat_id

    print("TEXT:", message.text)
    print("SENDER_CHAT:", message.sender_chat)
    print("FORWARD:", message.forward_from_chat)

    detected_channel_id = None
    channel_title = None

    # 📡 قناة مباشرة
    if message.sender_chat and message.sender_chat.type == "channel":
        detected_channel_id = message.sender_chat.id
        channel_title = message.sender_chat.title

    # 📡 forward
    elif message.forward_from_chat:
        detected_channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title

    # =============================
    # ❗ لا توجد قناة مرتبطة
    # =============================
    if group_id not in group_channels:
        if detected_channel_id:
            group_channels[group_id] = detected_channel_id

            await message.reply_text(
                f"✅ تم ربط القناة:\n{channel_title}\n\n"
                "🎯 الآن أرسل أي منشور طويل وسيتم تلخيصه"
            )

            print("✅ تم تسجيل القناة")
        else:
            # رسالة توجيه
            if message.text and message.text.startswith("/"):
                return

            await message.reply_text(
                "⚠️ لم يتم ربط قناة بعد\n\n"
                "📌 أرسل منشور من القناة (أو forward) لربطها"
            )
        return

    # =============================
    # ❌ قناة مختلفة
    # =============================
    if detected_channel_id and detected_channel_id != group_channels[group_id]:
        print("❌ قناة مختلفة")

        await message.reply_text(
            "❌ هذه ليست القناة المرتبطة\n"
            "⚠️ لا يمكن تغيير القناة بعد ربطها"
        )
        return

    # =============================
    # ❗ ليست رسالة قناة
    # =============================
    if not detected_channel_id:
        return

    # =============================
    # فلترة الرسائل
    # =============================
    if message.message_id in processed_messages:
        return

    if not message.text:
        return

    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    print("✅ تم التقاط الرسالة!")

    summary = summarize(message.text)

    await message.reply_text(f"قَالَ المُحَشِّي الفَاضِل:\n\n{summary}")

# =============================
# 🚀 تشغيل
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    print("✅ Bot is running...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
