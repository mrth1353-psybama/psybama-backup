import os
import requests

SMS_MODE = os.getenv('SMS_MODE', 'local')
FARAZSMS_BASE_URL = 'https://api.iranpayamak.com'
DEFAULT_SENDER = '90008361'


def _headers(api_key: str) -> dict:
    return {
        'Accept': 'application/json',
        'Api-Key': api_key,
        'Content-Type': 'application/json',
    }


def _sender() -> str:
    return os.getenv('FARAZSMS_SENDER', '').strip() or DEFAULT_SENDER


def _safe_json(response) -> dict:
    try:
        return response.json()
    except ValueError:
        return {'raw': response.text, 'status_code': response.status_code}


def send_otp(phone_number: str, otp_code: str) -> dict:
    mode = os.getenv('SMS_MODE', SMS_MODE)
    if mode == 'production':
        return _send_farazsms(phone_number, otp_code)
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

    api_key = os.getenv('SMS_API_KEY', '').strip()
    if not api_key:
        return {'success': False, 'error': 'SMS_API_KEY تنظیم نشده است'}

    url = f'{FARAZSMS_BASE_URL}/ws/v1/sms/simple'
    payload = {
        'text': message,
        'line_number': _sender(),
        'recipients': [phone_number],
        'number_format': 'english',
        'schedule': None,
    }
    try:
        response = requests.post(url, json=payload, headers=_headers(api_key), timeout=10)
        data = _safe_json(response)
        if data.get('status') == 'success':
            return {'success': True, 'mode': 'production'}
        return {'success': False, 'error': str(data.get('messages') or data)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _send_farazsms(phone_number: str, otp_code: str) -> dict:
    api_key = os.getenv('SMS_API_KEY', '').strip()
    if not api_key:
        raise ValueError("SMS_API_KEY برای فراز اس‌ام‌اس تنظیم نشده است")

    pattern_code = os.getenv('FARAZSMS_PATTERN', '').strip()
    if pattern_code:
        return _send_farazsms_pattern(phone_number, otp_code, api_key)
    return _send_farazsms_simple(phone_number, otp_code, api_key)


def _send_farazsms_pattern(phone_number: str, otp_code: str, api_key: str) -> dict:
    pattern_code = os.getenv('FARAZSMS_PATTERN', '').strip()
    pattern_var = os.getenv('FARAZSMS_PATTERN_VAR', 'code').strip() or 'code'

    url = f'{FARAZSMS_BASE_URL}/ws/v1/sms/pattern'
    payload = {
        'code': pattern_code,
        'attributes': {pattern_var: otp_code},
        'recipient': phone_number,
        'line_number': _sender(),
        'number_format': 'english',
    }
    try:
        response = requests.post(url, json=payload, headers=_headers(api_key), timeout=10)
        data = _safe_json(response)
        if data.get('status') == 'success':
            return {'success': True, 'mode': 'production'}
        raise RuntimeError(f"فراز اس‌ام‌اس خطا داد: {data.get('messages') or data}")
    except requests.RequestException as e:
        raise RuntimeError(f"خطای اتصال به فراز اس‌ام‌اس: {e}")


def _send_farazsms_simple(phone_number: str, otp_code: str, api_key: str) -> dict:
    message = f"کد تأیید سای‌باما:\n{otp_code}\nاین کد ۵ دقیقه اعتبار دارد."
    url = f'{FARAZSMS_BASE_URL}/ws/v1/sms/simple'
    payload = {
        'text': message,
        'line_number': _sender(),
        'recipients': [phone_number],
        'number_format': 'english',
        'schedule': None,
    }
    try:
        response = requests.post(url, json=payload, headers=_headers(api_key), timeout=10)
        data = _safe_json(response)
        if data.get('status') == 'success':
            return {'success': True, 'mode': 'production'}
        raise RuntimeError(f"فراز اس‌ام‌اس خطا داد: {data.get('messages') or data}")
    except requests.RequestException as e:
        raise RuntimeError(f"خطای اتصال به فراز اس‌ام‌اس: {e}")
