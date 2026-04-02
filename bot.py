import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# group_id -> {channel_id: channel_name}
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
                        "content": f"""لخص النص التالي في نقاط واضحة، واحرص على ما يلي في تلخيصك، أولًا أن يكون التلخيص مختصرًا وفي جمل قصيرة، وأن يكون التلخيص فصيحًا لغويًا، وأن يكون هناك مسافات مريحة للعين بين النقاط، وأن تورد تاريخ ولادة ووفاة من تذكره في التلخيص بين قوسين شرط أن تكون متأكدًا منه، ولا تطل في تلخيص النص فوق سبع نقاط، ولا تكتب أرقام النقاط فقط أدرجها، وتحدث بلغة موضوعية أي لا تبدأ جوابك بالقول إليك تلخيص النص أوحسنا فقط ابدأ بتلخيص النص :

{text}
"""
                    }
                ]
            }
        )

        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("❌ API ERROR:", e)

    return "❌ فشل التلخيص"

# =============================
# 👋 /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 حللت أهلًا ووطِئتَ سهلاً في بوت <b>المُحَشِّي</b>!\n\n"
        "📌 إليك طريقة عمله:\n"
        "1️⃣ أنزل البوت مشرفًا المجموعة المرتبطة بقناتك\n"
        "2️⃣ أرسل منشورً في قناتك\n\n"
        "✅ سيكون الربط تلقائيًا\n"
        "✍️ ها أنت ذا يُلَخَّص لك ما تشاء!\n\n"
        "⚠️ لفك الارتباط:\n"
        "أخرج البوت من مجموعة قناتك", parse_mode="HTML"
    )

# =============================
# 📥 استقبال الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    group_id = message.chat_id

    detected_channel_id = None
    channel_name = None

    # قناة مباشرة
    if message.sender_chat and message.sender_chat.type == "channel":
        detected_channel_id = message.sender_chat.id
        channel_name = message.sender_chat.title

    # forward
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
    f"فلمّا التمس منّي بعض الإخوة المقصّرين في العلم، والمنشغلين عنه بالفاني من المهلِكات، "
    f"أن ألخّص ما ورد في القناة المسمّاة: <b>{channel_name}</b>، أجبتُ مستعينًا بالله.",
    parse_mode="HTML"
)
    # =============================
    # لا توجد قناة
    # =============================
    if group_id not in group_channels:
        return

    if not detected_channel_id:
        return

    if detected_channel_id not in group_channels[group_id]:
        return

    if message.message_id in processed_messages:
        return

    if not message.text:
        return

    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    summary = summarize(message.text)

    await message.reply_text(
    f"<b>قَالَ المُحَشِّي الفَاضِل:</b>\n\n{summary}",
    parse_mode="HTML"
)

# =============================
# 🚀 تشغيل
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    print("✅ Bot running...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
