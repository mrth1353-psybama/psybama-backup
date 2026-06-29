import os
import requests

SMS_MODE = os.getenv('SMS_MODE', 'local')


def send_otp(phone_number: str, otp_code: str) -> dict:
    mode = os.getenv('SMS_MODE', SMS_MODE)
    if mode == 'local':
        return _send_local(phone_number, otp_code)
    elif mode == 'production':
        return _send_farazsms(phone_number, otp_code)
    else:
        return _send_local(phone_number, otp_code)


def _send_local(phone_number: str, otp_code: str) -> dict:
    print(f"[LOCAL SMS] Phone: {phone_number}  OTP: {otp_code}")
    return {
        'success': True,
        'mode': 'local',
        'display_otp': otp_code
    }


def send_sms(phone_number: str, message: str) -> dict:
    mode = os.getenv('SMS_MODE', SMS_MODE)
    if mode != 'production':
        print(f"[LOCAL SMS] Phone: {phone_number}\nMessage: {message}")
        return {'success': True, 'mode': 'local'}

    api_key  = os.getenv('SMS_API_KEY', '')
    sender   = os.getenv('FARAZSMS_SENDER', '3000******')
    username = os.getenv('FARAZSMS_USERNAME', '')
    url = 'https://ippanel.com/api/select'
    payload = {
        'op': 'send',
        'user': username,
        'pass': api_key,
        'fromNum': sender,
        'toNum': [phone_number],
        'message': message
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        if data.get('status') == 'OK' or response.status_code == 200:
            return {'success': True, 'mode': 'production'}
        return {'success': False, 'error': str(data)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _send_farazsms(phone_number: str, otp_code: str) -> dict:
    api_key = os.getenv('SMS_API_KEY', '')
    sender = os.getenv('FARAZSMS_SENDER', '3000******')
    pattern_code = os.getenv('FARAZSMS_PATTERN', '')

    if not api_key:
        raise ValueError("SMS_API_KEY برای فراز اس‌ام‌اس تنظیم نشده است")

    # اگر pattern_code تنظیم شده باشد → پیامک پترن (توصیه‌شده)
    if pattern_code:
        url = 'https://ippanel.com/api/select'
        payload = {
            'op': 'pattern',
            'user': os.getenv('FARAZSMS_USERNAME', ''),
            'pass': api_key,
            'fromNum': sender,
            'toNum': phone_number,
            'patternCode': pattern_code,
            'inputData': [{'otp': otp_code}]
        }
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        if data.get('status') == 'OK' or response.status_code == 200:
            return {'success': True, 'mode': 'production'}
        raise RuntimeError(f"فراز اس‌ام‌اس خطا داد: {data}")

    # پیامک ساده (بدون پترن)
    url = 'https://ippanel.com/api/select'
    message = f"کد تأیید سای‌باما:\n{otp_code}\nاین کد ۵ دقیقه اعتبار دارد."
    payload = {
        'op': 'send',
        'user': os.getenv('FARAZSMS_USERNAME', ''),
        'pass': api_key,
        'fromNum': sender,
        'toNum': [phone_number],
        'message': message
    }
    response = requests.post(url, json=payload, timeout=10)
    data = response.json()
    if data.get('status') == 'OK' or response.status_code == 200:
        return {'success': True, 'mode': 'production'}
    raise RuntimeError(f"فراز اس‌ام‌اس خطا داد: {data}")
