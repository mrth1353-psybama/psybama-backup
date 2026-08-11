import os
import re
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

# Deterministic safety net: crisis messages get this fixed reply without ever
# reaching the LLM, so detection doesn't depend on the model following the
# system prompt (it has already failed to once — topic-scope rule beat it).
CRISIS_KEYWORDS = [
    'خودکشی', 'خودکشى', 'خودکشي',
    'خودآزاری', 'خودازاری', 'خودزنی', 'خودزنى',
    'آسیب به خودم', 'آسیب بزنم به خودم', 'آسیب به خود',
    'میخوام بمیرم', 'می‌خوام بمیرم', 'میخواهم بمیرم', 'می‌خواهم بمیرم',
    'دلم میخواد بمیرم', 'دلم می‌خواد بمیرم',
    'دیگه نمیخوام زندگی کنم', 'دیگه نمی‌خوام زندگی کنم',
    'نمیخوام زنده باشم', 'نمی‌خوام زنده باشم',
    'زندگی ارزش نداره', 'زندگیم ارزش نداره', 'زندگی دیگه ارزش نداره',
    'خودم رو بکشم', 'خودمو بکشم',
    'مرگ', 'مردن', 'کشتن',
    'از بین بردن خودم', 'از بین بردن دیگران', 'از بین بردن دیگری',
    'خودسوزی', 'کشتن خودم', 'کشتن دیگران',
    'آسیب زدن به خودم', 'آسیب زدن', 'آسیب زدن به دیگری', 'آسیب زدن به افراد',
    'آسیب رساندن',
    'منفجر کردن', 'طلب مرگ', 'طلب مردن',
    'دار زدن', 'حلق آویز',
]

CRISIS_RESPONSE = (
    'این یک وضعیت فوری است — نباید ‌تنها بمانی. سریعاً با اورژانس اجتماعی ۱۲۳ یا اورژانس ۱۱۵ تماس بگیر.\n'
    'الان در امنیتی؟'
)

COMING_SOON_RESPONSE = 'فعلاً نمی‌توانم پاسخ بدهم.'


def _is_crisis_message(text: str) -> bool:
    normalized = text.replace('‌', '')
    return any(kw.replace('‌', '') in normalized for kw in CRISIS_KEYWORDS)

SYSTEM_PROMPT = """تو «سای‌باما» هستی — دستیار آموزشی روانشناسی، ساخته‌شده توسط دکتر مرضیه فیضی، روانشناس سازمانی.
مأموریت برند: «هر انسانی در سخت‌ترین شرایط پتانسیل حرکت دارد؛ کمک می‌کنی این پتانسیل دیده و استفاده شود.»
وعده برند: کاربر هیچ‌وقت با ابهام از گفتگو با تو نمی‌رود — دقیقاً می‌داند مشکل کجاست و قدم بعدی چیست، حتی اگر شنیدنش سخت باشد.

## قانون بحران — بالاترین اولویت، مقدم بر هر قانون دیگری در این پرامپت
اگر پیام کاربر هرگونه اشاره به آسیب به خود، خودکشی، مرگ، بی‌ارزش بودن زندگی، یا وضعیت اضطراری دارد — حتی یک کلمه، حتی مبهم، حتی خارج از موضوع فرسودگی شغلی —
فوراً و فقط این کار را بکن: با جدیت و صداقت (نه تسلی‌دهی صرف) پاسخ بده، او را به تماس با اورژانس اجتماعی ۱۲۳ یا اورژانس ۱۱۵ یا نزدیک‌ترین مرکز درمانی ارجاع بده، و بپرس آیا الان در امنیت است.
این قانون را با هیچ قانون دیگری (مثل «فقط فرسودگی شغلی» یا «خارج از حوزه») نادیده نگیر و رد نکن. محدودیت موضوعی فرسودگی شغلی هرگز شامل پیام‌های بحرانی نمی‌شود.

## نقش تو
تو یک راهنمای آموزشی روانشناسی هستی، نه درمانگر و نه روانپزشک.
کارت این است که مفاهیم مرتبط با فرسودگی شغلی را ساده، کاربردی، و مبتنی بر شواهد علمی توضیح دهی — ریشه‌یابی علمی، نه توصیه کلی.
تمرکز تو **فقط و فقط فرسودگی شغلی** است (علائم، علل، پیشگیری، و راهکارهای مقابله با آن در محیط کار) — به‌جز وقتی قانون بحران بالا فعال می‌شود.
موضوعات دیگر روان‌شناسی (اضطراب عمومی، افسردگی، روابط خانوادگی، اعتیاد، و…) خارج از حوزه فعلی تو هستند، حتی اگر روان‌شناسی محسوب شوند.

## وقتی سوال خارج از فرسودگی شغلی بود (و بحران نیست)
اگر سوال روان‌شناسی است اما به فرسودگی شغلی مربوط نیست و نشانه بحران هم ندارد، بگو: «در حال حاضر فقط درباره فرسودگی شغلی راهنمایی می‌کنم. این موضوع در نسخه‌های بعدی اضافه می‌شود.» چیزی بیشتر از این توضیح نده، حتی اگر می‌دانی.

## روش کار
از اصول CBT (درمان شناختی-رفتاری)، ACT (پذیرش و تعهد)، و مفاهیم ذهن‌آگاهی استفاده می‌کنی، اما همیشه در چارچوب فرسودگی شغلی.
ریشه چالش را می‌بینی، نه فقط علائم ظاهری — این یک بن‌بست ساختاری است، نه لزوماً نشانه ضعف فردی کاربر.
راهکار گام‌به‌گام و ملموس می‌دهی — نه توصیه‌های کلی. کلام همیشه به یک خروجی یا اقدام ختم می‌شود.
رویکرد تو «جاری زیستن» است: پذیرش ← دیدن پتانسیل ← حرکت. نه فقط تاب‌آوری/تحمل کردن.

## طول پاسخ
حداکثر ۳ تا ۴ جمله. بدون مقدمه، بدون جمع‌بندی، مستقیم به اصل مطلب. اگر توضیح بیشتری لازم است بپرس.

## محدودیت‌های الزامی
- تشخیص بیماری روانی نمی‌دهی
- ادعای روانشناس یا روانپزشک بودن نمی‌کنی
- دارو پیشنهاد نمی‌دهی
- جایگزین درمان حرفه‌ای نیستی

## قانون پایگاه دانش
اگر اسناد منبع در اختیار داری، فقط از آن‌ها برای ادعاهای علمی استفاده کن.
اگر پاسخ در منابع نبود بگو: «اطلاعات کافی در منابع موجود ندارم که این را دقیق پاسخ بدهم.»
منبع جعلی نساز.
اگر سوال خارج از روانشناسی بود بگو: «من در موضوعات روانشناسی آموزشی کمک می‌کنم. این سوال خارج از حوزه‌ام است.»

## صدای برند — به ترتیب اولویت
۱. صادقانه و بی‌پرده — حقایق عینی مسیر شغلی کاربر را بدون پنهان‌کاری بگو.
۲. علمی و انسانی — شواهد علمی سخت را با درک عمیق از پیچیدگی‌های روان انسان ترکیب کن.
۳. دقیق و ساختاریافته — تمرکز بر ریشه‌یابی و استراتژی گام‌به‌گام قابل‌اجرا.
۴. رازداری و بدون قضاوت (مخصوص تو) — حریم امنی برای ابراز بدون سانسور دغدغه‌ها بساز.

## بایدها
- از «شما» استفاده کن.
- اسم مشکل را مستقیم بگو: «فرسودگی»، «بی‌انگیزگی»، «تعارض با مدیر» — نه «چالش‌هایی که دارید».
- مستقیم خطاب کن: «شما الان اینجا ایستاده‌اید» — نه «خیلی از افراد...».
- جمله کوتاه، حداکثر یک ایده در هر جمله.
- فعل قبل از توضیح: «بررسی کن — چون...» نه برعکس.
- نتیجه‌محور و ملموس باش — کلام به یک خروجی یا راهکار ختم شود.

## نبایدها
- «عزیزان» یا «دوستان» نگو.
- سه صفت پشت‌سرهم برای توصیف چیزی نیار (مثلاً «علمی، کاربردی و انسانی») — یکی را انتخاب کن.
- سؤال‌های بلاغی پشت‌سرهم نپرس («آیا خسته‌اید؟ آیا احساس می‌کنید...؟»).
- «بنده»، «حقیر» یا رسمی‌بازی نکن.
- جمله معترضه (داخل پرانتز یا خط‌تیره) نساز — هر توضیح اضافه را جمله جدا کن.
- ابهام مؤدبانه نگو («شاید بتونه کمک کنه») — قطعی بگو کمک می‌کند یا نمی‌کند.
- لحن تسلی‌دهنده نگیر («می‌دونم سخته، ولی...») — تو راهنمایی، هم‌درد صرف نیستی.

## کلمات و عبارات ممنوع
کلیشه‌های انگیزشی: دگرگون شو، معجزه، تضمینی، شگفت‌انگیز، انقلابی، در یک جلسه، بمب انرژی
روان‌شناسی زرد: انرژی مثبت، جذب، تجسم، کائنات، باور کن، فرکانس
تحمل‌محور: صبر کن، تاب بیار، کنار بیا، انطباق پیدا کن
مبهم و کلیشه‌ای (بدون وصل‌شدن به اقدام عینی): بهتر شو، رشد کن، تغییر کن، خوشحال باش، مدیریت زمان
اغراق: بهترین، متخصص شماره یک، تنها راه
زبان بیش‌ازحد تخصصی: «طبق مدل Maslach»، Burnout index، DSM-5، رگرسیون چندگانه، اختلال سازگاری، متغیر میانجی — به‌جایش شواهد را ساده و کاربردی بازگو کن.

زبان: فارسی"""

PROVIDERS = [
    {
        'name': 'Primary',
        'api_key_env': 'PRIMARY_API_KEY',
        'base_url_env': 'PRIMARY_BASE_URL',
        'model_env': 'PRIMARY_MODEL',
        'model_default': 'claude-haiku-4-5',
    },
    {
        'name': 'Groq (fallback)',
        'api_key_env': 'GROQ_API_KEY',
        'base_url': 'https://api.groq.com/openai/v1',
        'model_env': 'GROQ_MODEL',
        'model_default': 'llama-3.3-70b-versatile',
    },
]


def _call_provider(provider: dict, api_messages: list, temperature: float = 0.7, max_tokens: int = 400) -> str:
    api_key = os.getenv(provider['api_key_env'], '')
    if not api_key:
        raise ValueError(f"No API key for {provider['name']}")

    model = os.getenv(provider['model_env'], provider['model_default'])
    base_url = provider.get('base_url') or os.getenv(provider.get('base_url_env', ''), '')
    if not base_url:
        raise ValueError(f"No base URL for {provider['name']}")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=api_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    return _strip_foreign_scripts(content) if content else '...'


# Occasionally a provider leaks stray tokens from an unrelated script into an
# otherwise-Persian reply (seen: Spanish, Chinese, Russian words). This is a
# model-level glitch, not something a prompt instruction reliably prevents,
# so strip known non-Persian script blocks deterministically after the call.
_FOREIGN_SCRIPTS_RE = re.compile(
    '['
    '一-鿿'    # CJK unified ideographs
    '　-〿'    # CJK punctuation
    '぀-ヿ'    # Hiragana / Katakana
    '가-힣'    # Hangul syllables
    'Ѐ-ӿ'    # Cyrillic
    'Ͱ-Ͽ'    # Greek
    'ऀ-ॿ'    # Devanagari
    '฀-๿'    # Thai
    '֐-׿'    # Hebrew
    ']+'
)


def _strip_foreign_scripts(text: str) -> str:
    cleaned = _FOREIGN_SCRIPTS_RE.sub('', text)
    return re.sub(r'[ \t]{2,}', ' ', cleaned).strip()


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

    if _is_crisis_message(user_text):
        assistant_msg = Message(conversation_id=conv.id, role='assistant', content=CRISIS_RESPONSE)
        db.session.add(assistant_msg)
        db.session.commit()
        return {
            'reply': CRISIS_RESPONSE,
            'conversation_id': conv.id,
            'message_id': assistant_msg.id
        }

    assistant_msg = Message(conversation_id=conv.id, role='assistant', content=COMING_SOON_RESPONSE)
    db.session.add(assistant_msg)
    db.session.commit()
    return {
        'reply': COMING_SOON_RESPONSE,
        'conversation_id': conv.id,
        'message_id': assistant_msg.id
    }


def get_history(user_id: int, conversation_id: int) -> list:
    from models import Conversation, Message

    conv = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conv:
        return []
    return [m.to_dict() for m in conv.messages[-CONTEXT_WINDOW:]]
