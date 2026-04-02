import os
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

MODELS = [ "qwen/qwen3.6-plus-preview:free", "qwen/qwen3.6-plus:free", "alibaba/wan-2.6", "openai/sora-2-pro", "google/veo-3.1"]
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# group_id -> {channel_id: channel_name}
group_channels = {}

# user_id -> set(group_ids)
user_groups = {}

processed_messages = set()

# =============================
# 🧠 التلخيص
# =============================
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

            if "choices" in data:
                result = data["choices"][0]["message"]["content"]
                if result.strip():
                    print(f"✅ Success with: {model}")
                    return result

            if "error" in data:
                print(f"❌ {model} failed:", data['error'].get("message"))

        except Exception as e:
            print(f"❌ Exception with {model}:", e)

    return "❌ فشل التلخيص (جميع الموديلات لم تعمل)"

# =============================
# 👋 /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📂 عرض قنواتي"]]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 حللت أهلًا ووطِئتَ سهلاً في بوت <b>المُحَشِّي</b>!\n\n"
        "اختر من القائمة 👇",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# =============================
# 📥 استقبال الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    group_id = message.chat_id

    # ✅ حفظ المستخدم ومجموعاته
    if message.from_user and not message.from_user.is_bot:
        user_id = message.from_user.id

        if user_id not in user_groups:
            user_groups[user_id] = set()

        user_groups[user_id].add(group_id)

    # =============================
    # زر عرض قنواتي
    # =============================
    if message.text == "📂 عرض قنواتي":
        user_id = message.from_user.id if message.from_user else None

        if not user_id or user_id not in user_groups:
            await message.reply_text("❌ لا توجد مجموعات مسجلة لك")
            return

        groups_list = user_groups[user_id]

        text = "📂 مجموعاتك التي تستخدم البوت:\n\n"

        for gid in groups_list:
            try:
                chat = await context.bot.get_chat(gid)
                text += f"• {chat.title}\n"
            except:
                text += "• مجموعة غير معروفة\n"

        await message.reply_text(text)
        return

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
    # شروط التلخيص
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
