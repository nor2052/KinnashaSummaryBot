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

# user_id -> set of channel usernames
user_channels = {}
MODELS = [ "qwen/qwen3.6-plus-preview:free", "qwen/qwen3.6-plus:free", "alibaba/wan-2.6", "openai/sora-2-pro", "google/veo-3.1"]
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# group_id -> {channel_id: channel_name}
group_channels = {}

processed_messages = set()

# =============================
# 🧠 التلخيص
# =============================
import requests

def summarize(text):
    for model in MODELS:
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
                            "content": f"""لخص النص التالي في نقاط واضحة، واحرص على ما يلي في تلخيصك، أولًا أن يكون التلخيص مختصرًا وفي جمل قصيرة، وأن يكون التلخيص فصيحًا لغويًا، وأن يكون هناك مسافات مريحة للعين بين النقاط، وأن تورد تاريخ ولادة ووفاة من تذكره في التلخيص بين قوسين شرط أن تكون متأكدًا منه، ولا تطل في تلخيص النص فوق سبع نقاط، ولا تكتب أرقام النقاط فقط أدرجها، وتحدث بلغة موضوعية أي لا تبدأ جوابك بالقول إليك تلخيص النص أو حسنا فقط ابدأ بتلخيص النص :

{text}
"""
                        }
                    ]
                },
                timeout=30
            )

            data = response.json()

            print(f"🔍 Trying model: {model}")
            print("Response:", data)

            # ✅ إذا نجح
            if "choices" in data:
                result = data["choices"][0]["message"]["content"]
                if result.strip():
                    print(f"✅ Success with: {model}")
                    return result

            # ❌ إذا فيه error
            if "error" in data:
                print(f"❌ {model} failed:", data['error'].get("message"))

        except Exception as e:
            print(f"❌ Exception with {model}:", e)

    return "❌ فشل التلخيص (جميع الموديلات لم تعمل)"



async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.effective_message

    if not message.text:
        return

    text = message.text.strip()

    if not text.startswith("@"):
        await message.reply_text("❌ أرسل يوزر القناة بهذا الشكل: @channel_username")
        return

    if user_id not in user_channels:
        user_channels[user_id] = set()

    user_channels[user_id].add(text.lower())

    await message.reply_text(f"✅ تم ربط القناة {text} بحسابك")    
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
        "أخرج البوت من مجموعة قناتك"
        "3️⃣ أرسل يوزر قناتك بهذا الشكل: @channel_username\n"
        , parse_mode="HTML"
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
# 🔒 التحقق من أن القناة مسموحة
# =============================
    if detected_channel_id and message.sender_chat:
        channel_username = message.sender_chat.username
    elif detected_channel_id and message.forward_from_chat:
        channel_username = message.forward_from_chat.username
    else:
        channel_username = None

    if not channel_username:
        return

    channel_username = "@" + channel_username.lower()

    # تحقق هل هذه القناة مسجلة عند أي مستخدم
    allowed = any(channel_username in channels for channels in user_channels.values())

    if not allowed:
        print("⛔ قناة غير مسموحة")
        return
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
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, add_channel))
    
    print("✅ Bot running...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
