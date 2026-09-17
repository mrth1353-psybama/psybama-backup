import os
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import session, jsonify

OTP_EXPIRY_MINUTES = 5
FIXED_TEST_OTP = '1234'


def generate_otp() -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def create_or_update_otp(phone_number: str):
    from models import db, User

    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        user = User(phone_number=phone_number)
        db.session.add(user)

    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    db.session.commit()
    return user, otp


def verify_otp(phone_number: str, submitted_code: str) -> tuple:
    from models import db, User

    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return False, 'user_not_found'

    sms_mode = os.getenv('SMS_MODE', 'local')

    if sms_mode == 'local' and submitted_code == FIXED_TEST_OTP:
        user.is_verified = True
        user.otp_code = None
        db.session.commit()
        return True, 'ok'

    if not user.otp_code:
        return False, 'no_otp_issued'
    if datetime.utcnow() > user.otp_expires_at:
        return False, 'otp_expired'
    if user.otp_code != submitted_code:
        return False, 'otp_mismatch'

    user.is_verified = True
    user.otp_code = None
    db.session.commit()
    return True, 'ok'


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'authentication_required', 'message': 'لطفاً ابتدا وارد شوید'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'admin_authentication_required', 'message': 'دسترسی مدیریت نیاز است'}), 403
        return f(*args, **kwargs)
    return decorated
