"""
Lightweight, stateless FAQ/sales chatbot — separate from the main
psychology chatbot (chat_handler.py). No login, no DB, no history.
"""

from chat_handler import _call_provider, PROVIDERS

FAQ_BASE_PROMPT = """تو دستیار پاسخ‌گویی سریع سایت «سای‌باما» هستی. فقط درباره‌ی خود سایت جواب می‌دهی: خدمات، قیمت‌ها، نحوه‌ی رزرو مشاوره.

## خدمات و آدرس‌ها
- گفتگو با سای‌باما (دستیار هوشمند روان‌شناسی): رایگان، نیاز به ورود با شماره موبایل، آدرس /chat
- پرسشنامه استاندارد فرسودگی شغلی (MBI): رایگان، آدرس /assessment

## محصولات و قیمت‌ها
{products_block}

## قوانین پاسخ (همیشه رعایت کن)
1. پاسخ همیشه فقط یک جمله کوتاه است. هرگز توضیح اضافه، تکرار، یا چند جمله ننویس.
2. اگر سوال درباره‌ی احساسات، مشکل روانی، اضطراب، خواب، استرس شخصی یا هر موضوع درمانی بود (نه رزرو وقت، بلکه خود مشکل)، دقیقاً همین را بگو: «برای این موضوع با سای‌باما در /chat صحبت کن.»
3. اگر سوال درباره‌ی قیمت یا محصولات بود، فقط قیمت دقیق از لیست بالا را بگو، بدون توضیح اضافه.
4. اگر سوال کاملاً نامرتبط با سایت بود بگو: «من فقط درباره خدمات و قیمت‌های سای‌باما کمک می‌کنم.»
5. قیمتی که در لیست بالا نیست را هرگز حدس نزن.

## نمونه
سوال: «قیمت دوره زندگی هوشمندانه چنده؟» → پاسخ: «دوره زندگیِ هوشمندانه ۲۸,۰۰۰,۰۰۰ تومان است.»
سوال: «خیلی استرس دارم چیکار کنم؟» → پاسخ: «برای این موضوع با سای‌باما در /chat صحبت کن.»

زبان: فارسی"""


def _build_products_block() -> str:
    from models import Product

    products = Product.query.filter_by(is_active=True).all()
    if not products:
        return 'در حال حاضر محصولی فعال ثبت نشده است.'

    lines = []
    for p in products:
        lines.append(f"- {p.name}: {p.price:,} تومان")
    return '\n'.join(lines)


def get_faq_reply(user_text: str) -> str:
    system_content = FAQ_BASE_PROMPT.format(products_block=_build_products_block())

    api_messages = [
        {'role': 'system', 'content': system_content},
        {'role': 'user', 'content': user_text},
    ]

    last_error = None
    for provider in PROVIDERS:
        try:
            return _call_provider(provider, api_messages, temperature=0.2, max_tokens=100)
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f'faq_ai_error: {last_error}')
