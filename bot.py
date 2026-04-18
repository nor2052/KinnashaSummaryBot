import os
import time
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

# =============================
# ⚙️ الإعدادات
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# جميع النماذج المتاحة (مرتبة حسب الأفضلية)
MODELS = [
    "canopylabs/orpheus-arabic-saudi",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct",
    "openai/gpt-oss-120b",
    "llama-3.1-8b-instant",
    "llama-3.2-90b-text-preview",
    "llama-3.1-70b-versatile",
    "groq/compound",
    "groq/compound-mini",
    "allam-2-7b",
    "canopylabs/orpheus-v1-english"
]

group_channels = {}
processed_messages = set()

# =============================
# 🧠 التلخيص باستخدام Groq
# =============================
def summarize(text, max_attempts=50):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    attempted_models = set()  # لتتبع النماذج التي جربناها
    
    for attempt in range(1, max_attempts + 1):
        for model in MODELS:
            if model in attempted_models:
                continue  # نتخطى النماذج التي جربناها سابقاً
                
            try:
                print(f"🔄 محاولة {attempt}/{max_attempts} باستخدام {model}")
                
                response = requests.post(
                    url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"""لخص النص التالي في نقاط واضحة، واحرص على ما يلي في تلخيصك، أولًا أن لخص النص التالي بشرط أن يكون عدد النقاط: من نقطة واحدة إلى 5 نقاط كحد أقصى. وأن يكون شكل النقاط كالتالي: - كل نقطة في سطر منفصل. - وتترك سطرًا فارغًا بين كل نقطة والتي تليها. وأن يكون أسلوب الكتابة كالتالي - استخدم جملًا قصيرة. -وتستخدم لغة عربية فصيحة. ولا تبدأ بأي كلمات مثل "إليك التلخيص" أو "حسنًا" أو "تلخيص النص يأتي في النقاط التالية:" أو ما يشابهها، فقط اكتب النقاط مباشرة. وأن يضاف المحتوى التالي للتلخيص:  -إذا ذكرت شخصًا وتعلمت تاريخ ميلاده ووفاته بيقين، فاكتبهما بين قوسين هكذا (الميلاد - الوفاة). - واشرح بإيجاز معنى المصطلح الأكثر تكرارًا في النص.
{text}
"""
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 600
                    },
                    timeout=60
                )
                
                print(f"📡 الحالة: {response.status_code}")
                
                # معالجة حالة تجاوز الحد
                if response.status_code == 429:
                    print(f"⚠️ تجاوز حد الاستخدام للنموذج {model}")
                    attempted_models.add(model)
                    continue
                
                if response.status_code != 200:
                    print(f"❌ خطأ: {response.text[:100]}")
                    attempted_models.add(model)
                    continue
                
                data = response.json()
                result = data["choices"][0]["message"]["content"]
                
                if result and result.strip():
                    print(f"✅ نجح التلخيص باستخدام {model}")
                    return result
                else:
                    print(f"⚠️ النموذج {model} أعاد محتوى فارغاً")
                    attempted_models.add(model)
                    
            except Exception as e:
                print(f"❌ خطأ مع {model}: {e}")
                attempted_models.add(model)
                continue
        
        # بعد الانتهاء من جميع النماذج في هذه المحاولة
        if len(attempted_models) >= len(MODELS):
            print(f"⚠️ تم استنفاذ جميع النماذج في المحاولة {attempt}")
            if attempt < max_attempts:
                wait_time = 10  # ننتظر أطول قبل إعادة المحاولة
                print(f"⏳ ننتظر {wait_time} ثوانٍ قبل إعادة المحاولة...")
                attempted_models.clear()  # نمسح القائمة لنعيد التجربة
                time.sleep(wait_time)
        elif attempt < max_attempts:
            wait_time = 2
            print(f"⏳ ننتظر {wait_time} ثوانٍ قبل المحاولة التالية...")
            time.sleep(wait_time)
    
    return "❌ فشل التلخيص بعد استخدام جميع النماذج المتاحة"

# =============================
# 👋 /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 حللت أهلًا ووطِئتَ سهلاً في بوت <b>المُحَشِّي</b>!\n\n"
        "📌 إليك طريقة عمله:\n"
        "1️⃣ أنزل البوت مشرفًا المجموعة المرتبطة بقناتك\n"
        "2️⃣ أرسل منشورًا في قناتك يزيد على 100 كلمة\n\n"
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
    
    # حالة منشور من قناة
    if message.sender_chat and message.sender_chat.type == "channel":
        detected_channel_id = message.sender_chat.id
        channel_name = message.sender_chat.title
    
    # حالة forward من قناة
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
                f"فلمّا التمس منّي بعض الإخوة المقصّرين في العلم، والمنشغلين عنه، "
                f"أن ألخّص ما ورد في القناة: <b>{channel_name}</b>، أجبتُ مستعينًا بالله.",
                parse_mode="HTML"
            )
    
    # =============================
    # التحقق من الشروط
    # =============================
    if group_id not in group_channels:
        return
    
    if not detected_channel_id:
        return
    
    if detected_channel_id not in group_channels[group_id]:
        return
    
    if message.message_id in processed_messages:
        return
    
    # دعم النصوص والصور مع نص
    text = message.text or message.caption
    
    if not text:
        return
    
    if len(text.split()) < 100:
        return
    
    processed_messages.add(message.message_id)
    
    # =============================
    # 🧠 التلخيص
    # =============================
    summary = summarize(text)
    
    await message.reply_text(
        f"<b>قَالَ المُحَشِّي الفَاضِل:</b>\n\n{summary}",
        parse_mode="HTML"
    )

# =============================
# 🚀 تشغيل البوت
# =============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_messages))
    
    print(f"✅ Bot running with {len(MODELS)} Groq models...")
    print(f"📋 النماذج المتاحة: {', '.join(MODELS[:5])}...")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
