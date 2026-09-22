import os
import requests

SANDBOX = os.getenv('ZARINPAL_SANDBOX', 'true').lower() == 'true'


def plog(msg):
    """لاگ پرداخت — هم در stdout و هم در فایلی که قابل بررسی باشد."""
    print(msg, flush=True)
    try:
        log_path = os.path.join(os.path.dirname(__file__), 'payment_debug.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception:
        pass

if SANDBOX:
    REQUEST_URL  = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
    VERIFY_URL   = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'
    STARTPAY_URL = 'https://sandbox.zarinpal.com/pg/StartPay/{}'
else:
    REQUEST_URL  = 'https://api.zarinpal.com/pg/v4/payment/request.json'
    VERIFY_URL   = 'https://api.zarinpal.com/pg/v4/payment/verify.json'
    STARTPAY_URL = 'https://www.zarinpal.com/pg/StartPay/{}'


def create_payment(amount_tomans, description, callback_url):
    merchant_id = os.getenv('ZARINPAL_MERCHANT_ID')
    if not merchant_id:
        return {'success': False, 'error': 'مرچنت‌کد زرین‌پال تنظیم نشده است.'}
    try:
        res = requests.post(REQUEST_URL, json={
            'merchant_id': merchant_id,
            'amount': amount_tomans * 10,  # Rials
            'description': description,
            'callback_url': callback_url,
        }, timeout=15)
        data = res.json().get('data', {})
        if data.get('code') == 100:
            authority = data['authority']
            plog(f"[ZARINPAL] request OK status={res.status_code} amount(Rial)={amount_tomans * 10} code=100 authority={authority}")
            return {'success': True, 'authority': authority, 'pay_url': STARTPAY_URL.format(authority)}
        errors = res.json().get('errors', {})
        plog(f"[ZARINPAL] request rejected. status={res.status_code} amount(Rial)={amount_tomans * 10} "
             f"data={res.json().get('data')} errors={errors}")
        return {'success': False, 'error': errors.get('message', 'خطا در اتصال به درگاه')}
    except Exception as e:
        plog(f"[ZARINPAL] request exception: {type(e).__name__}: {e}")
        return {'success': False, 'error': 'خطا در اتصال به درگاه پرداخت. لطفاً از روش کارت به کارت استفاده کنید.'}


def verify_payment(authority, amount_tomans):
    merchant_id = os.getenv('ZARINPAL_MERCHANT_ID')
    if not merchant_id:
        return {'success': False, 'error': 'مرچنت‌کد زرین‌پال تنظیم نشده است.'}
    try:
        res = requests.post(VERIFY_URL, json={
            'merchant_id': merchant_id,
            'amount': amount_tomans * 10,
            'authority': authority,
        }, timeout=15)
        data = res.json().get('data', {})
        code = data.get('code')
        if code in (100, 101):
            return {'success': True, 'ref_id': str(data.get('ref_id', ''))}
        return {'success': False, 'error': 'پرداخت تأیید نشد'}
    except Exception:
        return {'success': False, 'error': 'خطا در تأیید پرداخت'}
