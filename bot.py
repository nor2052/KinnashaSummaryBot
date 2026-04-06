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

def summarize(text, max_attempts=10):
    """
    تحاول التلخيص حتى 10 مرات باستخدام نماذج مختلفة
    إذا نجحت في أي محاولة، تعيد النتيجة فورًا
    """
    for attempt in range(1, max_attempts + 1):
        for model in MODELS:
            try:
                print(f"🔄 المحاولة {attempt}/{max_attempts} - جاري تجربة النموذج: {model}")
                
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://t.me/your_bot",
                        "X-Title": "Telegram Summary Bot"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"""لخص النص التالي في نقاط واضحة، واحرص على ما يلي في تلخيصك، أولًا أن يكون التلخيص مختصرًا وفي جمل قصيرة، وأن يكون التلخيص فصيحًا لغويًا، وأن يكون هناك مسافات مريحة للعين بين النقاط، وأن تورد تاريخ ولادة ووفاة من تذكره في التلخيص بين قوسين شرط أن تكون متأكدًا منه، وشرح المصطلح الأكثر استعمالًا، ولا تطل في تلخيص النص فوق ست نقاط، ولا تكتب النقاط فقط أدرجها، وتحدث بلغة موضوعية أي لا تبدأ جوابك بالقول إليك تلخيص النص أو حسنا فقط ابدأ بتلخيص النص :

{text}
"""
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    },
                    timeout=60
                )

                print(f"   📡 رد الخادم: {response.status_code}")

                if response.status_code == 429:
                    # حد الاستخدام - سنحاول مرة أخرى لاحقًا
                    print(f"   ⚠️ تم تجاوز حد الاستخدام (429)، سننتظر قليلًا ثم نعيد المحاولة...")
                    break  # نخرج من حلقة النماذج وننتقل إلى المحاولة التالية

                if response.status_code != 200:
                    print(f"   ❌ خطأ HTTP {response.status_code}: {response.text[:100]}")
                    continue  # جرب النموذج التالي

                data = response.json()

                if "error" in data:
                    print(f"   ❌ خطأ من API: {data['error'].get('message', 'غير معروف')}")
                    continue

                if "choices" in data and len(data["choices"]) > 0:
                    result = data["choices"][0]["message"]["content"]
                    if result and result.strip():
                        print(f"   ✅ نجح التلخيص في المحاولة {attempt} باستخدام النموذج: {model}")
                        return result
                    else:
                        print(f"   ⚠️ النموذج {model} أعاد محتوى فارغًا")
                else:
                    print(f"   ⚠️ استجابة النموذج {model} لا تحتوي على 'choices'")

            except requests.exceptions.Timeout:
                print(f"   ⏰ انتهت المهلة مع النموذج {model}")
                continue
            except requests.exceptions.RequestException as e:
                print(f"   📡 خطأ في الطلب مع {model}: {e}")
                continue
            except Exception as e:
                print(f"   💥 خطأ غير متوقع مع {model}: {e}")
                continue

        # إذا وصلنا إلى هنا، فشلت كل النماذج في هذه المحاولة
        if attempt < max_attempts:
            wait_time = 3  # ننتظر 3 ثوانٍ بين المحاولات
            print(f"⏳ فشلت المحاولة {attempt}، ننتظر {wait_time} ثوانٍ قبل المحاولة {attempt + 1}...")
            import time
            time.sleep(wait_time)

    return "❌ فشل التلخيص بعد 10 محاولات متتالية. يرجى المحاولة لاحقًا."
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
