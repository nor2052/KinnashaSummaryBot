import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
OPENAI_API_KEY = "PUT_YOUR_API_KEY_HERE"

processed_messages = set()

def summarize(text):
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4.1-mini",
            "input": f"لخص النص التالي في 3 نقاط قصيرة:\n{text}"
        }
    )

    try:
        return response.json()["output"][0]["content"][0]["text"]
    except:
        return "❌ حدث خطأ أثناء التلخيص"

async def handle_pinned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message and message.pinned_message:
        original = message.pinned_message

        if not original.text:
            return

        if original.message_id in processed_messages:
            return

        text = original.text

        if len(text.split()) < 75:
            return

        processed_messages.add(original.message_id)

        summary = summarize(text)

        await message.reply_text(f"📌 التلخيص:\n\n{summary}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, handle_pinned))

print("✅ Bot is running...")
app.run_polling()