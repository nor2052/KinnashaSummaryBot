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
# 👋 /start + أزرار
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 عرض القنوات", callback_data="status")],
        [InlineKeyboardButton("🔓 فك ارتباط قناة", callback_data="unlink_menu")]
    ]

    await update.message.reply_text(
        "👋 مرحبًا بك في بوت التلخيص!\n\n"
        "📌 أضف البوت إلى مجموعة وأرسل منشور من قناة لبدء الربط.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# 📊 عرض القنوات
# =============================
async def show_status(query):
    group_id = query.message.chat.id

    if group_id not in group_channels or not group_channels[group_id]:
        await query.edit_message_text("❌ لا توجد قنوات مرتبطة")
        return

    text = "📡 القنوات المرتبطة:\n\n"
    for ch_name in group_channels[group_id].values():
        text += f"- {ch_name}\n"

    await query.edit_message_text(text)

# =============================
# 🔓 قائمة فك الارتباط
# =============================
async def unlink_menu(query):
    group_id = query.message.chat.id

    if group_id not in group_channels or not group_channels[group_id]:
        await query.edit_message_text("❌ لا توجد قنوات لفك ارتباطها")
        return

    keyboard = []

    for ch_id, ch_name in group_channels[group_id].items():
        keyboard.append([
            InlineKeyboardButton(
                f"❌ {ch_name}",
                callback_data=f"unlink_{ch_id}"
            )
        ])

    await query.edit_message_text(
        "اختر القناة التي تريد فك ارتباطها:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# ❌ تنفيذ فك الارتباط
# =============================
async def unlink_channel(query):
    group_id = query.message.chat.id
    channel_id = int(query.data.split("_")[1])

    if group_id in group_channels and channel_id in group_channels[group_id]:
        channel_name = group_channels[group_id][channel_id]

        del group_channels[group_id][channel_id]

        await query.edit_message_text(
            f"✅ تم فك ارتباط القناة:\n{channel_name}"
        )
    else:
        await query.edit_message_text("❌ القناة غير موجودة")

# =============================
# 🎯 التعامل مع الأزرار
# =============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "status":
        await show_status(query)

    elif query.data == "unlink_menu":
        await unlink_menu(query)

    elif query.data.startswith("unlink_"):
        await unlink_channel(query)

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

    # لا توجد قناة
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
