"""مدیریت کدهای تخفیف فروشگاه.

کدهای تخفیف حساس نباید در ریپازیتوری عمومی باشند؛ بنابراین منبع اصلی،
متغیر محیطی DISCOUNT_CODES_JSON است (در .env سرور تنظیم می‌شود). ساختار:

DISCOUNT_CODES_JSON={"MODIR90": {"active": true, "type": "percent", "value": 90, "product": "کتاب مدیر هوشمند"}}

فایل discounts.json فقط به‌عنوان fallback برای محیط محلی نگه داشته شده و نباید
کد راز واقعی داشته باشد. تغییر در هر درخواست خوانده می‌شود (نیازی به
ری‌استارت نیست)؛ فقط بعد از تغییر .env، سرویس ری‌استارت لازم است.
"""
import json
import os
from pathlib import Path

DISCOUNTS_FILE = Path(__file__).parent / 'discounts.json'


def _load_from_env():
    raw = os.getenv('DISCOUNT_CODES_JSON', '')
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    if not isinstance(data, dict) or 'codes' not in data:
        return None
    return data


def load_discounts():
    data = _load_from_env()
    if data is not None:
        return data
    try:
        with open(DISCOUNTS_FILE, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return {'codes': {}}
    if not isinstance(data, dict) or 'codes' not in data:
        return {'codes': {}}
    return data


def evaluate_discount(code, product):
    """کد را بررسی می‌کند و دیکتی با جزئیات تخفیف برمی‌گرداند یا None."""
    if not code or not product:
        return None
    code = code.strip()
    if not code:
        return None

    entry = load_discounts().get('codes', {}).get(code)
    if not entry:
        return None
    if not entry.get('active', True):
        return None

    target = entry.get('product')
    if target and product.name != target:
        return None

    price = product.price
    if entry.get('type') == 'amount':
        discount = min(int(entry.get('value', 0)), price)
        final = price - discount
        percent = None
    else:
        percent = float(entry.get('value', 0))
        discount = int(round(price * percent / 100))
        final = price - discount

    return {
        'code': code,
        'type': entry.get('type', 'percent'),
        'value': entry.get('value'),
        'discount_amount': discount,
        'final_amount': final,
        'original_amount': price,
        'percent': percent,
    }
