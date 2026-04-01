import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

group_channels = {}
REQUIRED_CHANNEL = "nst3li8"

# ✅ تحقق الاشتراك
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=f"@{REQUIRED_CHANNEL}",
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🧠 التلخيص
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
                "messages": [{
                    "role": "user",
                    "content": f"لخص هذا النص في نقاط واضحة ومنسقة:\n\n{text}"
                }]
            }
        )

        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return "❌ فشل التلخيص"

    except Exception as e:
        print(e)
        return "❌ خطأ في التلخيص"

# 🚀 start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 اشترك", url=f"https://t.me/{REQUIRED_CHANNEL}")],
        [InlineKeyboardButton("✅ تحقق", callback_data="check")]
    ]

    await update.message.reply_text(
        "🔒 يجب الاشتراك أولاً",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 🔘 تحقق
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_subscribed(query.from_user.id, context):
        await query.edit_message_text(
            "✅ تم التحقق\n\nأضفني لمجموعة وأرسل يوزر القناة"
        )
    else:
        await query.answer("❌ لم تشترك", show_alert=True)

# 📥 تحديد القناة (مرة واحدة فقط)
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message.chat.type == "private":
        return

    if not message.text.startswith("@"):
        return

    group_id = message.chat_id

    # ❗ منع التغيير
    if group_id in group_channels:
        await message.reply_text("⚠️ تم تعيين قناة مسبقًا ولا يمكن تغييرها")
        return

    username = message.text.replace("@", "").lower()
    group_channels[group_id] = username

    await message.reply_text(f"✅ تم التفعيل للقناة @{username}")

# 📡 التقاط رسائل القناة (مهم جدًا)
async def handle_channel_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    if not message.sender_chat:
        return

    group_id = message.chat_id

    if group_id not in group_channels:
        return

    target = group_channels[group_id]

    sender = message.sender_chat.username

    if not sender:
        return

    if sender.lower() != target:
        return

    if not message.text:
        return

    if len(message.text.split()) < 50:
        return

    print("📌 تم اكتشاف رسالة من القناة")

    summary = summarize(message.text)

    reply = f"""
<b>كَمَا قَالَ المُحَشِّي الفَاضِل:</b>

{summary}
"""

    await message.reply_text(reply, parse_mode="HTML")

# 🚀 تشغيل
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check, pattern="check"))

    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, set_channel))

    # 🔥 مهم جدًا: ALL وليس TEXT فقط
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, handle_channel_posts))

    print("✅ Bot running...")

    app.run_polling()

if __name__ == "__main__":
    main()
