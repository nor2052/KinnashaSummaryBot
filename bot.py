import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)
import subprocess
import sys

try:
    import lara_sdk
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lara-sdk"])
    import lara_sdk

try:
    from mistralai import Mistral
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mistralai"])
from mistralai.client import Mistral

from lara_sdk import Translator, Credentials

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LARA_ACCESS_KEY_ID = os.getenv("LARA_ACCESS_KEY_ID")
LARA_ACCESS_KEY_SECRET = os.getenv("LARA_ACCESS_KEY_SECRET")

LANGUAGETOOL_URL = "https://api.languagetool.org/v2/check"

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

TRANSLATE_LANGUAGES = {
    "ar": "🇸🇦 العربية",
    "en": "🇬🇧 الإنجليزية",
    "fr": "🇫🇷 الفرنسية",
    "es": "🇪🇸 الإسبانية",
    "de": "🇩🇪 الألمانية",
    "tr": "🇹🇷 التركية",
    "ru": "🇷🇺 الروسية"
}

GRAMMAR_LANGUAGES = {
    "ar": "🇸🇦 العربية",
    "en-US": "🇺🇸 الإنجليزية",
    "fr": "🇫🇷 الفرنسية",
    "es": "🇪🇸 الإسبانية",
    "de": "🇩🇪 الألمانية"
}

group_channels = {}
processed_messages = set()

def query_groq(prompt_content, max_attempts=50, max_tokens=600):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    attempted_models = set()
    
    for attempt in range(1, max_attempts + 1):
        for model in MODELS:
            if model in attempted_models:
                continue
                
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": prompt_content}
                        ],
                        "temperature": 0.3,
                        "max_tokens": max_tokens
                    },
                    timeout=60
                )
                
                if response.status_code == 429:
                    attempted_models.add(model)
                    continue
                
                if response.status_code != 200:
                    attempted_models.add(model)
                    continue
                
                data = response.json()
                result = data["choices"][0]["message"]["content"]
                
                if result and result.strip():
                    return result
                else:
                    attempted_models.add(model)
                    
            except Exception:
                attempted_models.add(model)
                continue
        
        if len(attempted_models) >= len(MODELS):
            if attempt < max_attempts:
                attempted_models.clear()
                time.sleep(5)
        elif attempt < max_attempts:
            time.sleep(2)
    
    return "❌ فشل الاتصال بالنظام الذكي بعد عدة محاولات."

def summarize(text):
    prompt = f"""لخص النص التالي في مجموعة نقاط واضحة متماسكة، واحرص على ما يلي في تلخيصك، أولًا أن لخص النص التالي بشرط أن يكون عدد النقاط: من نقطة واحدة إلى 5 نقاط كحد أقصى. وأن يكون شكل النقاط كالتالي: - كل نقطة في سطر منفصل. - وتترك سطرًا فارغًا بين كل نقطة والتي تليها. وأن يكون أسلوب الكتابة كالتالي - استخدم جملًا قصيرة. -وتستخدم لغة عربية فصيحة. ولا تبدأ بأي كلمات مثل "إليك التلخيص" أو "حسنًا" أو "تلخيص النص يأتي في النقاط التالية:" أو ما يشابهها، فقط اكتب النقاط مباشرة. وأن يضاف المحتوى التالي للتلخيص:  -إذا ذكرت شخصًا وتعلمت تاريخ ميلاده ووفاته بيقين، فاكتبهما بين قوسين هكذا (الميلاد - الوفاة). - واشرح بإيجاز معنى المصطلح الأكثر تكرارًا في النص.
{text}
"""
    return query_groq(prompt, max_tokens=600)

def translate_with_lara(text, target_lang="ar", source_lang="en"):
    if not LARA_ACCESS_KEY_ID or not LARA_ACCESS_KEY_SECRET:
        return "❌ مفاتيح Lara API غير مضبوطة. يرجى إعداد LARA_ACCESS_KEY_ID و LARA_ACCESS_KEY_SECRET"

    try:
        credentials = Credentials(access_key_id=LARA_ACCESS_KEY_ID, access_key_secret=LARA_ACCESS_KEY_SECRET)
        lara = Translator(credentials)

        if not source_lang or source_lang == "auto":
            source_lang = "en"

        result = lara.translate(
            text,
            source=source_lang,
            target=target_lang
        )

        return result.translation

    except Exception as e:
        return f"❌ خطأ في الترجمة عبر Lara: {str(e)}"

def check_grammar(text, language="ar"):
    url = LANGUAGETOOL_URL
    data = {
        "text": text,
        "language": language
    }
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            matches = result.get("matches", [])
            if not matches:
                return "✅ لا توجد أخطاء نحوية أو إملائية مكتشفة في النص!"
            
            errors_list = []
            for i, match in enumerate(matches[:10], 1):
                msg = match.get("message", "خطأ محتمل")
                context_str = match.get("context", {}).get("text", "")
                replacements = [r.get("value", "") for r in match.get("replacements", [])[:3]]
                
                err_fmt = f"<b>{i}. {msg}</b>\n📝 <i>السياق:</i> {context_str}"
                if replacements:
                    err_fmt += f"\n💡 <i>الاقتراحات:</i> {', '.join(replacements)}"
                errors_list.append(err_fmt)
            
            return "\n\n".join(errors_list)
        else:
            return f"❌ خطأ في التدقيق: {response.status_code}"
    except Exception as e:
        return f"❌ خطأ عند الاتصال بخدمة التدقيق: {str(e)}"

def query_mistral(prompt_content, max_tokens=300):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return "❌ مفتاح MISTRAL_API_KEY غير مضبوط في المتغيرات البيئية. يرجى الحصول على مفتاح من https://console.mistral.ai/api-keys/"

    models = [
        "mistral-small-latest",
        "mistral-medium-latest",
        "mistral-large-latest",
        "open-mistral-7b",
        "open-mixtral-8x7b"
    ]
    
    debug_logs = []

    try:
        client = Mistral(api_key=api_key.strip())

        for model in models:
            try:
                chat_response = client.chat.complete(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt_content
                        }
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens
                )
                
                result = chat_response.choices[0].message.content
                if result and result.strip():
                    return result.strip()

            except Exception as e:
                error_msg = str(e)
                if "402" in error_msg:
                    debug_logs.append(f"النموذج {model}: يتطلب دفع (تحقق من رصيدك)")
                elif "429" in error_msg:
                    debug_logs.append(f"النموذج {model}: تجاوزت حد المعدل (انتظر ثم حاول مجدداً)")
                elif "401" in error_msg:
                    debug_logs.append(f"النموذج {model}: مفتاح API غير صالح")
                else:
                    debug_logs.append(f"النموذج {model}: {error_msg}")
                continue

    except Exception as e:
        return f"❌ خطأ في تهيئة عميل Mistral: {str(e)}"

    error_details = "\n".join(debug_logs)
    return f"❌ فشل الاتصال بخدمة Mistral.\n\n<b>التفاصيل التقنية:</b>\n<code>{error_details}</code>"

def format_citation(text, last_citation=None):
    prompt = f"""أنت بوت متخصص في توثيق المصادر وفق التالي.
قواعدك هي:
1. لا تضيف أي معلومات غير موجودة في النص المدخل.
2. الترتيب الثابت هو: بقية اسم المؤلف، اسم المؤلف الأول، السنة، المترجم (إن وجد)، العنوان (بين __)، الطبعة، الناشر، المكان، الصفحات.
3. للكتب: استخدم القالب: بقية اسم المؤلف، اسم المؤلف الأول. (السنة). ترجمة المترجم. __العنوان__ (ط. الرقم). المكان: الناشر. (ص. الرقم).
4. للوحات: استخدم القالب: بقية اسم الفنان، اسم الفنان الأول. (السنة). __عنوان العمل__.
5. إذا وردت عبارة "المصدر السابق نفسه"، أرجع إلى آخر مصدر تم توثيقه وأعد توثيقه مع تغيير رقم الصفحة فقط.
6. حافظ على اللغة المطلوبة (عربية أو إنجليزية).
7. لا تترجم العناوين أو الأسماء، بل احتفظ بها كما هي.
8. إذا كان هناك عنصر ناقص (سنة، ناشر، طبعة)، تجاوزه ولا تذكره.
9. استخدم __ حول العنوان في كل الحالات.

آخر مصدر تم توثيقه سابقاً (استخدمه إذا وردت عبارة "المصدر السابق نفسه"):
{last_citation if last_citation else "لا يوجد مصدر سابق"}

النص المطلوب توثيقه:
{text}

رد بالتوثيق المطلوب فقط دون أي مقدمات أو شروحات.
"""
    return query_mistral(prompt, max_tokens=300)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    
    welcome_text = (
        "👋 <b>حللت أهلًا ووطِئتَ سهلاً في بوت المُحَشِّي!</b>\n\n"
        "اختر إحدى الخدمات التالية للبدء:\n\n"
        "1️⃣ <b>التلخيص:</b> كيفية ربط البوت بالقناة لتلخيص المنشورات تلقائياً.\n"
        "2️⃣ <b>الترجمة:</b> لترجمة النصوص عبر Lara Translate.\n"
        "3️⃣ <b>التدقيق:</b> لفحص الأخطاء النحوية والإملائية.\n"
        "4️⃣ <b>التوثيق:</b> لترتيب المصادر والكتب وأسماء اللوحات وفق APA.\n"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📝 التلخيص", callback_data="btn_summary_info"),
            InlineKeyboardButton("🌐 الترجمة", callback_data="btn_translate")
        ],
        [
            InlineKeyboardButton("✍️ التدقيق", callback_data="btn_grammar"),
            InlineKeyboardButton("📖 التوثيق", callback_data="btn_citation")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "btn_summary_info":
        info_text = (
            "📌 <b>طريقة عمل التلخيص التلقائي:</b>\n\n"
            "1️⃣ أنزل البوت مشرفًا المجموعة المرتبطة بقناتك\n"
            "2️⃣ أرسل منشورًا في قناتك يزيد على 100 كلمة\n\n"
            "✅ سيكون الربط تلقائيًا\n"
            "✍️ ها أنت ذا يُلَخَّص لك ما تشاء!\n\n"
            "⚠️ لفك الارتباط:\n"
            "أخرج البوت من مجموعة قناتك"
        )
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]
        await query.edit_message_text(info_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "btn_translate":
        context.user_data["mode"] = "waiting_for_translate_text"
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]
        await query.edit_message_text(
            "🌐 <b>قسم الترجمة (Lara Translate):</b>\n\n"
            "الرجاء إرسال النص الذي تريد ترجمته الآن...",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data.startswith("tr_lang_"):
        target_lang = data.replace("tr_lang_", "")
        text = context.user_data.get("pending_text")
        if not text:
            keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]]
            await query.edit_message_text(
                "❌ انتهت صلاحية النص، يرجى البدء من جديد.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return
        
        await query.edit_message_text("⏳ جاري الترجمة باستخدام Lara...")
        translated = translate_with_lara(text, target_lang=target_lang, source_lang="auto")
        
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]]
        await query.edit_message_text(
            f"<b>🌐 نتيجة الترجمة:</b>\n\n{translated}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data == "btn_grammar":
        context.user_data["mode"] = "waiting_for_grammar_text"
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]
        await query.edit_message_text(
            "🔍 <b>قسم التدقيق النحوي:</b>\n\n"
            "الرجاء إرسال النص الذي تريد تدقيقه نحوياً وإملائياً...",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data.startswith("gr_lang_"):
        lang = data.replace("gr_lang_", "")
        text = context.user_data.get("pending_text")
        if not text:
            keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]]
            await query.edit_message_text(
                "❌ انتهت صلاحية النص، يرجى البدء من جديد.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return

        await query.edit_message_text("⏳ جاري التدقيق النحوي...")
        result = check_grammar(text, language=lang)
        
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]]
        await query.edit_message_text(
            f"<b>🔍 نتيجة التدقيق النحوي:</b>\n\n{result}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data == "btn_citation":
        context.user_data["mode"] = "waiting_for_citation_text"
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]
        await query.edit_message_text(
            "📚 <b>قسم توثيق المصادر:</b>\n\n"
            "أرسل معلومات الكتاب أو اللوحة الفنية المراد توثيقها وفق المعايير الأكاديمية.\n"
            "<i>(ملاحظة: يمكنك استخدام عبارة 'المصدر السابق نفسه' للإشارة لآخر مصدر وثقته).</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data == "main_menu":
        await start(update, context)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    mode = context.user_data.get("mode")
    text = message.text or message.caption

    if mode == "waiting_for_grammar_text" and text:
        context.user_data["pending_text"] = text
        context.user_data["mode"] = None
        
        keyboard = []
        row = []
        for code, name in GRAMMAR_LANGUAGES.items():
            row.append(InlineKeyboardButton(name, callback_data=f"gr_lang_{code}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")])
        
        await message.reply_text(
            "🔍 <b>اختر لغة التدقيق:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    if mode == "waiting_for_translate_text" and text:
        context.user_data["pending_text"] = text
        context.user_data["mode"] = None

        keyboard = []
        row = []
        for code, name in TRANSLATE_LANGUAGES.items():
            row.append(InlineKeyboardButton(name, callback_data=f"tr_lang_{code}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")])

        await message.reply_text(
            "🌐 <b>اختر اللغة المراد الترجمة إليها:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    if mode == "waiting_for_citation_text" and text:
        context.user_data["mode"] = None
        waiting_msg = await message.reply_text("⏳ جاري تنظيم التوثيق وفق القواعد...")
        
        last_cite = context.user_data.get("last_citation")
        formatted = format_citation(text, last_citation=last_cite)
        
        if "❌" not in formatted:
            context.user_data["last_citation"] = formatted
        
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]]
        await waiting_msg.edit_text(
            f"<code>{formatted}</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
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

    if group_id in group_channels and detected_channel_id in group_channels[group_id]:
        if message.message_id not in processed_messages and text and len(text.split()) >= 100:
            processed_messages.add(message.message_id)
            summary = summarize(text)
            await message.reply_text(
                f"<b>قَالَ المُحَشِّي الفَاضِل:</b>\n\n{summary}",
                parse_mode="HTML"
            )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL, handle_messages))
    
    print("✅ البوت يعمل بنجاح")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
