# Telegram Multi-Service Bot

هذا مشروع بوت تلغرام -مكتوب بمساعدة الذكاء الاصطناعي- يقدم أربع خدمات متكاملة: التلخيص التلقائي لمنشورات القنوات داخل المجموعات، الترجمة الفورية باستخدام Lara Translate، التدقيق النحوي والإملائي عبر LanguageTool، وتوثيق المصادر والمراجع وفق المعايير الأكاديمية. الفكرة الأساسية هي توفير أدوات تحريرية ونحوية متكاملة في بوت واحد، مع إمكانية ربطه بالقنوات لتلخيص المحتوى تلقائياً.

This is a Telegram bot -written by AI model- that provides four integrated services: automatic summarization of channel posts inside groups, instant translation using Lara Translate, grammatical and spelling checking via LanguageTool, and academic citation formatting. The main idea is to offer comprehensive editing and linguistic tools in one bot, with automatic channel post summarization capability.

## How it works

يقوم البوت بتقديم واجهة تفاعلية عبر الأزرار، ويستجيب للأوامر التالية:
- التلخيص: يراقب المنشورات القادمة من القنوات في المجموعات، ويسجل القناة تلقائياً عند أول منشور، ثم يلخص النصوص الطويلة (أكثر من 100 كلمة) بنقاط مختصرة
- الترجمة: يستقبل النص من المستخدم، ثم يعرض قائمة باللغات المتاحة للترجمة، ويستخدم Lara Translate SDK للترجمة الفورية
- التدقيق النحوي: يستقبل النص، ويسمح باختيار اللغة، ثم يفحص الأخطاء النحوية والإملائية عبر LanguageTool API ويعرض الاقتراحات التصحيحية
- التوثيق: يستقبل معلومات الكتاب أو اللوحة الفنية، وينظمها وفق قالب أكاديمي موحد مع إمكانية استخدام "المصدر السابق نفسه" لتكرار التوثيق

The bot provides an interactive button-based interface and responds to the following commands:
- Summarization: Monitors channel posts in groups, auto-registers channels upon first post, and summarizes long texts (100+ words) in bullet points
- Translation: Accepts text from user, displays available language options, and uses Lara Translate SDK for instant translation
- Grammar Check: Accepts text, allows language selection, then checks grammatical and spelling errors via LanguageTool API with correction suggestions
- Citation: Accepts book or artwork information, formats it according to unified academic standards with "same as previous source" capability for repeated citations

## Requirements

- Python 3.11.9
- Telegram Bot Token
- Groq API Key (for summarization)
- Mistral API Key (for citation formatting)
- Lara Translate credentials (ACCESS_KEY_ID and ACCESS_KEY_SECRET)

## Installation

```bash
pip install python-telegram-bot requests mistralai lara-sdk
```
