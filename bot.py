import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 🔐 القناة المطلوبة
REQUIRED_CHANNEL = "@nst3li8"

group_channels = {}
processed_messages = set()

# =============================
# 🔔 أزرار الاشتراك
# =============================
def subscription_buttons():
    keyboard = [
        [InlineKeyboardButton("🔔 اشترك في القناة", url="https://t.me/nst3li8")],
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

# =============================
# 🔍 التحقق من الاشتراك
# =============================
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# =============================
# 🧠 التلخيص (محسّن)
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
                        "role": "system",
                        "content": "أنت مساعد ذكي متخصص في التلخيص الاحترافي."
                    },
                    {
                        "role": "user",
                        "content": f"""
لخص النص التالي بأسلوب احترافي:

- استخدم نقاط واضحة
- اجعل الجمل قصيرة
- استخرج الأفكار الأساسية فقط
- لا تضف شرح من عندك

النص:
{text}
"""
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
# 📥 استقبال الرسائل
# =============================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔥 UPDATE RECEIVED")

    message = update.message
    if not message:
        print("❌ لا يوجد message")
        return

    user_id = message.from_user.id

    # 🔐 تحقق الاشتراك
    if not await is_subscribed(user_id, context):
        await message.reply_text(
            "🚫 يجب الاشتراك في القناة أولاً لاستخدام البوت",
            reply_markup=subscription_buttons()
        )
        return

    group_id = message.chat_id

    # 🔍 عرض كل شيء للتشخيص
    print("TEXT:", message.text)
    print("SENDER_CHAT:", message.sender_chat)
    print("FORWARD:", message.forward_from_chat)

    # =============================
    # 📌 تسجيل القناة (مرة واحدة)
    # =============================
    if message.sender_chat and message.sender_chat.type == "channel":
        if group_id not in group_channels:
            group_channels[group_id] = message.sender_chat.id
            print("✅ تم تسجيل القناة:", message.sender_chat.title)

    # =============================
    # ❗️ إذا لم تسجل قناة → خروج
    # =============================
    if group_id not in group_channels:
        print("❌ لا توجد قناة مسجلة")
        return

    target_channel_id = group_channels[group_id]
    detected_channel_id = None

    # قناة مباشرة
    if message.sender_chat and message.sender_chat.type == "channel":
        detected_channel_id = message.sender_chat.id

    # forward
    elif message.forward_from_chat:
        detected_channel_id = message.forward_from_chat.id

    if not detected_channel_id:
        print("❌ ليست رسالة قناة")
        return

    print("📡 Detected:", detected_channel_id)
    print("🎯 Target:", target_channel_id)

    if detected_channel_id != target_channel_id:
        print("❌ قناة مختلفة")
        return

    if message.message_id in processed_messages:
        return

    if not message.text:
        print("❌ لا يوجد نص")
        return

    if len(message.text.split()) < 75:
        print("❌ النص قصير")
        return

    processed_messages.add(message.message_id)

    print("✅ تم التقاط الرسالة!")

    summary = summarize(message.text)

    await message.reply_text(
        f"📌 *التلخيص:*\n\n{summary}",
        parse_mode="Markdown"
    )

# =============================
# 🔘 التعامل مع الأزرار
# =============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "check_sub":
        if await is_subscribed(user_id, context):
            await query.edit_message_text("✅ تم التحقق! يمكنك الآن استخدام البوت 🎉")
        else:
            await query.answer("❌ لم تشترك بعد!", show_alert=True)

# =============================
# 🚀 تشغيل
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, handle_messages))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot is running...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

# ✅ إصلاح الخطأ
if __name__ == "__main__":
    main()
