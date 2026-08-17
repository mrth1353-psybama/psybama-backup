import os
import requests

SANDBOX = os.getenv('ZARINPAL_SANDBOX', 'true').lower() == 'true'

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
            return {'success': True, 'authority': authority, 'pay_url': STARTPAY_URL.format(authority)}
        errors = res.json().get('errors', {})
        return {'success': False, 'error': errors.get('message', 'خطا در اتصال به درگاه')}
    except Exception:
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
