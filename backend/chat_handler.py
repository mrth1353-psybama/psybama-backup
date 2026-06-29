import os
import uuid
import httpx

# Fix: openai 1.40 passes 'proxies' to httpx 0.28 which no longer accepts it
_orig_client_init = httpx.Client.__init__
def _patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxies', None)
    _orig_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_client_init

from openai import OpenAI

CONTEXT_WINDOW = 20

SYSTEM_PROMPT = """تو «سای‌باما» هستی — دستیار آموزشی روانشناسی، ساخته‌شده توسط دکتر مرضیه فیضی، روانشناس سازمانی.

## نقش تو
تو یک راهنمای آموزشی روانشناسی هستی، نه درمانگر و نه روانپزشک.
کارت این است که مفاهیم روانشناسی را ساده، کاربردی، و مبتنی بر شواهد علمی توضیح دهی.
تمرکز اصلی‌ات: فرسودگی شغلی، سلامت روان در محیط کار ایران، و مهارت‌های تفکر شناختی.

## روش کار
از اصول CBT (درمان شناختی-رفتاری)، ACT (پذیرش و تعهد)، و مفاهیم ذهن‌آگاهی استفاده می‌کنی.
ریشه چالش را می‌بینی، نه فقط علائم ظاهری.
راهکار گام‌به‌گام و ملموس می‌دهی — نه توصیه‌های کلی.

## طول پاسخ
حداکثر ۳ تا ۴ جمله. بدون مقدمه، بدون جمع‌بندی، مستقیم به اصل مطلب. اگر توضیح بیشتری لازم است بپرس.

## محدودیت‌های الزامی
- تشخیص بیماری روانی نمی‌دهی
- ادعای روانشناس یا روانپزشک بودن نمی‌کنی
- دارو پیشنهاد نمی‌دهی
- جایگزین درمان حرفه‌ای نیستی
- در بحران (آسیب به خود، وضعیت اضطراری): با همدلی پاسخ بده و به اورژانس اجتماعی ۱۲۳ یا متخصص ارجاع بده

## قانون پایگاه دانش
اگر اسناد منبع در اختیار داری، فقط از آن‌ها برای ادعاهای علمی استفاده کن.
اگر پاسخ در منابع نبود بگو: «اطلاعات کافی در منابع موجود ندارم که این را دقیق پاسخ بدهم.»
منبع جعلی نساز.
اگر سوال خارج از روانشناسی بود بگو: «من در موضوعات روانشناسی آموزشی کمک می‌کنم. این سوال خارج از حوزه‌ام است.»

## سبک گفتگو (هویت برند سای‌باما)
- از «تو» استفاده کن (صمیمی اما محترمانه)
- جملات کوتاه — یک ایده در هر جمله
- اسم مشکل را مستقیم بگو: «فرسودگی»، «بی‌انگیزگی»، «تعارض با مدیر»
- مستقیم و صادق باش — نه تسلی‌دهنده صرف
- این برند راهنماست، نه همدرد محض

## کلمات ممنوع
هرگز استفاده نکن: معجزه، تضمینی، شگفت‌انگیز، انقلابی، دگرگون شو، در یک جلسه، انرژی مثبت، کائنات، باور کن، فرکانس، تاب بیار، کنار بیا، بهتر شو، رشد کن، عزیزان، دوستان، شاید بتونه کمک کنه

زبان: فارسی"""

PROVIDERS = [
    {
        'name': 'Groq',
        'api_key_env': 'GROQ_API_KEY',
        'base_url': 'https://api.groq.com/openai/v1',
        'model_env': 'GROQ_MODEL',
        'model_default': 'llama-3.3-70b-versatile',
    },
]


def _call_provider(provider: dict, api_messages: list) -> str:
    api_key = os.getenv(provider['api_key_env'], '')
    if not api_key:
        raise ValueError(f"No API key for {provider['name']}")

    model = os.getenv(provider['model_env'], provider['model_default'])

    client = OpenAI(api_key=api_key, base_url=provider['base_url'])
    response = client.chat.completions.create(
        model=model,
        messages=api_messages,
        temperature=0.7,
        max_tokens=400,
    )
    content = response.choices[0].message.content
    return content or '...'


def build_context(conversation_id: int) -> list:
    from models import Message

    messages = (Message.query
                .filter_by(conversation_id=conversation_id)
                .order_by(Message.timestamp.desc())
                .limit(CONTEXT_WINDOW)
                .all())
    messages.reverse()
    return [{'role': m.role, 'content': m.content} for m in messages]


def send_message(user_id: int, user_text: str, conversation_id: int = None) -> dict:
    from models import db, Message, Conversation
    from rag_handler import get_relevant_context

    if conversation_id:
        conv = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conv:
            return {'error': 'conversation_not_found'}
    else:
        conv = Conversation(user_id=user_id, session_id=uuid.uuid4().hex)
        db.session.add(conv)
        db.session.flush()

    user_msg = Message(conversation_id=conv.id, role='user', content=user_text)
    db.session.add(user_msg)
    db.session.flush()

    context = build_context(conv.id)

    rag_context = get_relevant_context(user_text)
    system_content = SYSTEM_PROMPT
    if rag_context:
        system_content += f"\n\nمنابع مرتبط از پایگاه دانش:\n{rag_context}"

    api_messages = [{'role': 'system', 'content': system_content}] + context

    reply_text = None
    last_error = None

    for provider in PROVIDERS:
        try:
            reply_text = _call_provider(provider, api_messages)
            print(f'[AI] OK via {provider["name"]}')
            break
        except Exception as e:
            print(f'[AI] {provider["name"]} failed: {type(e).__name__}: {e}')
            last_error = e
            continue

    if reply_text is None:
        db.session.rollback()
        return {'error': f'ai_error: {last_error}'}

    assistant_msg = Message(conversation_id=conv.id, role='assistant', content=reply_text)
    db.session.add(assistant_msg)
    db.session.commit()

    return {
        'reply': reply_text,
        'conversation_id': conv.id,
        'message_id': assistant_msg.id
    }


def get_history(user_id: int, conversation_id: int) -> list:
    from models import Conversation, Message

    conv = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conv:
        return []
    return [m.to_dict() for m in conv.messages[-CONTEXT_WINDOW:]]
