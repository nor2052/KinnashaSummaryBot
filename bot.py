import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

REQUIRED_CHANNEL = "nst3li8"

# الربط الاحترافي
channel_group_map = {}   # channel -> group
group_channel_map = {}   # group -> channel

processed_messages = set()

# 🧠 التلخيص
def summarize(text):
    models = [
        "qwen/qwen3.6-plus-preview:free",
        "bytedance/seedance-1-5-pro"
    ]

    text = text[:3000]

    for model in models:
        try:
            print(f"🔄 Trying model: {model}")

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
                            "content": f"قم بتلخيص النص التالي في نقاط، ضع فراغًا بين نقطة وأخرى واكتبه بطريقة تجعله مقروءًا وفي حال كان اقتباسًا قصيرًا لخصه بجملة واحدة صارمة ولا تكتب أي بداية من عندك فقط ابدأ بكتابة التلخيص:\n\n{text}"
                        }
                    ]
                }
            )

            data = response.json()
            print("📊 RESPONSE:", data)

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            print("❌ Summarize error:", e)

    return "❌ فشل التلخيص"

# ✅ التحقق من الاشتراك
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=f"@{REQUIRED_CHANNEL}",
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]

    except Exception as e:
        print("❌ Subscription error:", e)
        return False

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(user_id, context):
        await update.message.reply_text(
            f"❌ اشترك أولاً:\nhttps://t.me/{REQUIRED_CHANNEL}"
        )
        return

    await update.message.reply_text(
        "✅ جاهز\n\n"
        "📌 الخطوات:\n"
        "1- أضف البوت لمجموعة\n"
        "2- اجعله مشرف\n"
        "3- أرسل يوزر القناة داخل المجموعة"
    )

# 📌 تسجيل القناة داخل المجموعة
async def register_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # لازم داخل مجموعة
    if message.chat.type not in ["group", "supergroup"]:
        return

    text = message.text.strip()

    if not text.startswith("@"):
        return

    group_id = message.chat.id
    channel_username = text.replace("@", "")

    print(f"📥 محاولة ربط: {channel_username} -> {group_id}")

    # ❌ المجموعة مربوطة مسبقًا
    if group_id in group_channel_map:
        print("⚠️ Group already linked")
        return

    # ❌ القناة مستخدمة
    if channel_username in channel_group_map:
        print("⚠️ Channel already used")
        return

    try:
        chat = await context.bot.get_chat(f"@{channel_username}")

        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)

        if bot_member.status not in ["administrator", "creator"]:
            await message.reply_text("❌ اجعل البوت مشرف في القناة أولاً")
            return

        # ✅ تسجيل
        channel_group_map[channel_username] = group_id
        group_channel_map[group_id] = channel_username

        await message.reply_text(f"✅ تم ربط القناة @{channel_username}")

        print("✅ Linked successfully")

    except Exception as e:
        print("❌ Register error:", e)
        await message.reply_text("❌ فشل ربط القناة")

# 📥 استقبال الرسائل
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.sender_chat:
        return

    group_id = message.chat.id
    channel_username = message.sender_chat.username

    # تحقق أن هذه المجموعة مرتبطة بهذه القناة
    if group_id not in group_channel_map:
        return

    if group_channel_map[group_id] != channel_username:
        return

    if message.message_id in processed_messages:
        return

    if not message.text:
        return

    if len(message.text.split()) < 75:
        return

    processed_messages.add(message.message_id)

    print(f"📌 Processing: {channel_username} in group {group_id}")

    summary = summarize(message.text)

    try:
        await message.reply_text(f"قَالَ المُحَشِّي الفَاضِل::\n\n{summary}")
    except Exception as e:
        print("❌ Reply error:", e)

# 🚀 تشغيل
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            register_channel
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            handle_messages
        )
    )

    print("✅ Bot running...")

    app.run_polling()

if __name__ == "__main__":
    main()
