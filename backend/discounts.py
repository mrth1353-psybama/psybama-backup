"""مدیریت کدهای تخفیف فروشگاه از طریق فایل discounts.json.

برای تغییر میزان تخفیف یا کد، کافی است فایل discounts.json را ویرایش کنید
(نیازی به ری‌استارت سرور نیست — فایل در هر درخواست خوانده می‌شود):

{
  "codes": {
    "MODIR90": {
      "active": true,                 // false کد را غیرفعال می‌کند
      "type": "percent",              // "percent" (درصدی) یا "amount" (مبلغ ثابت تومان)
      "value": 90,                    // ۹۰ یعنی ۹۰٪ تخفیف
      "product": "کتاب مدیر هوشمند"   // نام دقیق محصولی که کد روی آن اعمال می‌شود
    }
  }
}
"""
import json
from pathlib import Path

DISCOUNTS_FILE = Path(__file__).parent / 'discounts.json'


def load_discounts():
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
