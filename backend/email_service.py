import os
import smtplib
from email.message import EmailMessage

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() in ('1', 'true', 'yes')


def _smtp_settings():
    return {
        'host': os.getenv('SMTP_HOST', ''),
        'port': int(os.getenv('SMTP_PORT', '587') or 587),
        'username': os.getenv('SMTP_USERNAME', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'from_addr': os.getenv('SMTP_FROM', ''),
        'use_ssl': os.getenv('SMTP_USE_SSL', 'false').lower() in ('1', 'true', 'yes'),
    }


def _send(subject: str, body: str) -> dict:
    if not EMAIL_ENABLED:
        print(f"[LOCAL EMAIL] Subject: {subject}\n{body}")
        return {'success': True, 'mode': 'local'}

    s = _smtp_settings()
    recipients = [addr.strip() for addr in os.getenv('NOTIFY_EMAIL', '').split(',') if addr.strip()]
    if not s['host'] or not recipients:
        print(f"[EMAIL NOT CONFIGURED] Subject: {subject}\n{body}")
        return {'success': False, 'error': 'SMTP or NOTIFY_EMAIL not configured'}

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = s['from_addr'] or s['username']
    msg['To'] = ', '.join(recipients)
    msg.set_content(body)

    try:
        if s['use_ssl']:
            server = smtplib.SMTP_SSL(s['host'], s['port'], timeout=15)
        else:
            server = smtplib.SMTP(s['host'], s['port'], timeout=15)
            server.starttls()
        if s['username']:
            server.login(s['username'], s['password'])
        server.send_message(msg)
        server.quit()
        return {'success': True, 'mode': 'production'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_contact_notification(name: str, phone: str, message: str) -> dict:
    subject = f'درخواست مشاوره جدید — {name}'
    body = (
        'درخواست مشاوره جدید از سایت سای‌باما ثبت شد:\n\n'
        f'نام: {name}\n'
        f'شماره تماس: {phone}\n'
        f'متن درخواست: {message or "(بدون پیام)"}\n'
        '\nبرای پاسخ، شماره تماس را از همین پیام بگیرید.'
    )
    return _send(subject, body)


def send_webinar_registration_notification(name: str, email: str, phone: str,
                                           webinar_title: str, webinar_date: str) -> dict:
    subject = f'ثبت‌نام جدید در وبینار «{webinar_title}» — {name or phone}'
    body = (
        'یک ثبت‌نام جدید در وبینار رایگان سایت سای‌باما انجام شد:\n\n'
        f'وبینار: {webinar_title}\n'
        f'تاریخ برگزاری: {webinar_date or "(تعیین نشده)"}\n\n'
        f'نام: {name or "(وارد نشده)"}\n'
        f'شماره تماس: {phone}\n'
        f'ایمیل: {email or "(وارد نشده)"}\n'
        '\nجزئیات کامل در پنل مدیریت بخش «ثبت‌نامی‌های وبینار» موجود است.'
    )
    return _send(subject, body)


def send_career_intake_notification(answers: dict) -> dict:
    lines = []
    for item in answers['answers']:
        val = item['a']
        if len(val) > 500:
            val = val[:500] + '…'
        lines.append(f"{item['q']}:\n  {val}")
    body = '\n\n'.join(lines)
    subject = f'فرم پذیرش کوچینگ شغلی جدید — {answers["answers"][0]["a"]}'
    full_body = (
        'فرم جدید پذیرش کوچینگ شغلی در سایت سای‌باما ثبت شد.\n\n'
        + body
        + '\n\nجزئیات کامل در پنل مدیریت بخش «فرم پذیرش شغلی» موجود است.'
    )
    return _send(subject, full_body)


def send_org_intake_notification(answers: dict) -> dict:
    lines = []
    for item in answers['answers']:
        val = item['a']
        if len(val) > 500:
            val = val[:500] + '…'
        lines.append(f"{item['q']}:\n  {val}")
    body = '\n\n'.join(lines)
    subject = f'فرم پذیرش کوچینگ سازمانی جدید — {answers["answers"][0]["a"]}'
    full_body = (
        'فرم جدید پذیرش کوچینگ سازمانی در سایت سای‌باما ثبت شد.\n\n'
        + body
        + '\n\nجزئیات کامل در پنل مدیریت بخش «فرم پذیرش سازمانی» موجود است.'
    )
    return _send(subject, full_body)
