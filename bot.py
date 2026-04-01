import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
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
                        "content": f"""لخص النص التالي في نقاط واضحة:

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
    keyboard = [
        [InlineKeyboardButton("📊 عرض القنوات", callback_data="status")]
    ]

    await update.message.reply_text(
        "👋 مرحبًا بك في بوت التلخيص!\n\n"
        "📌 الاستخدام:\n"
        "1️⃣ أضف البوت إلى مجموعة\n"
        "2️⃣ أرسل منشور من قناة داخل المجموعة\n\n"
        "✅ سيتم ربط القناة تلقائيًا\n"
        "✍️ بعدها سيتم تلخيص أي منشور طويل\n\n"
        "⚠️ ملاحظة:\n"
        "لفك الارتباط قم بإزالة القناة أو إعادة إضافة البوت",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# 📊 عرض القنوات
# =============================
async def show_status(query):
    group_id = query.message.chat.id

    if group_id not in group_channels or not group_channels[group_id]:
        await safe_edit(query, "❌ لا توجد قنوات مرتبطة")
        return

    text = "📡 القنوات المرتبطة:\n\n"
    for ch_name in group_channels[group_id].values():
        text += f"- {ch_name}\n"

    text += "\n⚠️ لفك الارتباط احذف القناة أو أعد إضافة البوت"

    await safe_edit(query, text)

# =============================
# 🛡️ حل مشكلة timeout
# =============================
async def safe_edit(query, text):
    try:
        await query.answer()
    except:
        pass  # تجاهل الخطأ

    try:
        await query.edit_message_text(text)
    except Exception as e:
        print("❌ Edit error:", e)

# =============================
# 🎯 الأزرار
# =============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "status":
        await show_status(query)

# =============================
# 📥 الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    group_id = message.chat_id

    detected_channel_id = None
    channel_name = None

    if message.sender_chat and message.sender_chat.type == "channel":
        detected_channel_id = message.sender_chat.id
        channel_name = message.sender_chat.title

    elif message.forward_from_chat:
        detected_channel_id = message.forward_from_chat.id
        channel_name = message.forward_from_chat.title

    # تسجيل القناة
    if detected_channel_id:
        if group_id not in group_channels:
            group_channels[group_id] = {}

        if detected_channel_id not in group_channels[group_id]:
            group_channels[group_id][detected_channel_id] = channel_name

            await message.reply_text(f"✅ تم ربط القناة:\n{channel_name}")

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

    await message.reply_text(f"📌 التلخيص:\n\n{summary}")

# =============================
# 🚀 تشغيل
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    print("✅ Bot running...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
