import os
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

# =============================
# ⚙️ الإعدادات
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODELS = [
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-3.2-90b-text-preview"
]
# group_id -> {channel_id: channel_name}
group_channels = {}

processed_messages = set()

# =============================
# 🧠 التلخيص باستخدام Groq
# =============================
import requests


def summarize(text, max_attempts=100):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(1, max_attempts + 1):
        for model in MODELS:
            try:
                print(f"🔄 محاولة {attempt}/{max_attempts} باستخدام {model}")

                response = requests.post(
                    url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"""لخص النص التالي في نقاط واضحة، واحرص على ما يلي في تلخيصك، أولًا أن يكون التلخيص مختصرًا وفي جمل قصيرة، وأن يكون التلخيص فصيحًا لغويًا، وأن يكون هناك مسافات مريحة للعين بين النقاط، وأن تورد تاريخ ولادة ووفاة من تذكره في التلخيص بين قوسين شرط أن تكون متأكدًا منه، وشرح المصطلح الأكثر استعمالًا، ولا تطل في تلخيص النص فوق ست نقاط، ولا تكتب النقاط فقط أدرجها، وتحدث بلغة موضوعية أي لا تبدأ جوابك بالقول إليك تلخيص النص أو حسنا فقط ابدأ بتلخيص النص 
{text}
"""
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 800
                    },
                    timeout=60
                )

                print(f"📡 الحالة: {response.status_code}")

                if response.status_code != 200:
                    print(response.text)
                    continue

                data = response.json()
                result = data["choices"][0]["message"]["content"]

                if result and result.strip():
                    print("✅ نجح التلخيص")
                    return result

            except Exception as e:
                print(f"❌ خطأ: {e}")
                continue

    return "❌ فشل التلخيص بعد عدة محاولات"
# =============================
# 👋 /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 حللت أهلًا ووطِئتَ سهلاً في بوت <b>المُحَشِّي</b>!\n\n"
        "📌 إليك طريقة عمله:\n"
        "1️⃣ أنزل البوت مشرفًا المجموعة المرتبطة بقناتك\n"
        "2️⃣ أرسل منشورًا في قناتك يزيد على 75 كلمة\n\n"
        "✅ سيكون الربط تلقائيًا\n"
        "✍️ ها أنت ذا يُلَخَّص لك ما تشاء!\n\n"
        "⚠️ لفك الارتباط:\n"
        "أخرج البوت من مجموعة قناتك", parse_mode="HTML"
    )

# =============================
# 📥 استقبال الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    group_id = message.chat_id

    detected_channel_id = None
    channel_name = None

    # حالة منشور من قناة
    if message.sender_chat and message.sender_chat.type == "channel":
        detected_channel_id = message.sender_chat.id
        channel_name = message.sender_chat.title

    # حالة forward من قناة
    elif message.forward_from_chat:
        detected_channel_id = message.forward_from_chat.id
        channel_name = message.forward_from_chat.title

    # =============================
    # تسجيل القناة
    # =============================
    if detected_channel_id:
        if group_id not in group_channels:
            group_channels[group_id] = {}

        if detected_channel_id not in group_channels[group_id]:
            group_channels[group_id][detected_channel_id] = channel_name

            await message.reply_text(
                f"<b>أما بعد:</b>\n"
                f"فلمّا التمس منّي بعض الإخوة المقصّرين في العلم، والمنشغلين عنه، "
                f"أن ألخّص ما ورد في القناة: <b>{channel_name}</b>، أجبتُ مستعينًا بالله.",
                parse_mode="HTML"
            )

    # =============================
    # التحقق من الشروط
    # =============================
    if group_id not in group_channels:
        return

    if not detected_channel_id:
        return

    if detected_channel_id not in group_channels[group_id]:
        return

    if message.message_id in processed_messages:
        return

    text = message.text or message.caption

    if not text:
        return

    if len(text.split()) < 75:
        return

    processed_messages.add(message.message_id)
    # =============================
    # 🧠 التلخيص
    # =============================
    summary = summarize(text)


    await message.reply_text(
        f"<b>قَالَ المُحَشِّي الفَاضِل:</b>\n\n{summary}",
        parse_mode="HTML"
    )

# =============================
# 🚀 تشغيل البوت
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    print("✅ Bot running with Groq...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()