# Telegram Summarizer Bot

هذا مشروع بسيط لبوت تلغرام -مكتوب بمساعدة الذكاء الاصطناعي- يقوم بتلخيص المنشورات الطويلة القادمة من القنوات داخل المجموعات. الفكرة الأساسية هي التقاط الرسائل المرسلة من قناة (سواء بشكل مباشر أو عبر إعادة توجيه)، ثم إرسال نص مختصر وواضح على شكل نقاط.

This is a simple Telegram bot -written by AI model- that summarizes long posts coming from channels inside groups. The main idea is to detect channel messages (either directly or forwarded), then generate a short and clear bullet-point summary.

## How it works

يقوم البوت بمراقبة الرسائل داخل المجموعة:
- عند إرسال منشور من قناة، يتم تسجيل القناة تلقائيًا
- إذا كان النص طويلًا بما يكفي، يتم إرساله إلى نموذج لغوي
- يعاد التلخيص في شكل نقاط مختصرة

The bot listens to messages in a group:
- When a channel post is detected, the channel gets registered automatically
- If the message is long enough, it is sent to a language model
- A short bullet-point summary is returned

## Requirements

- Python 3.11.9
- Telegram Bot Token
- OpenRouter API Key

## Installation

```bash
pip install python-telegram-bot requests
