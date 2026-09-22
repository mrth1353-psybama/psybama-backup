import threading
from flask import Blueprint, render_template, request, jsonify
from models import db, CareerIntake, OrgIntake
from limiter_config import limiter

intake_bp = Blueprint('intake', __name__)

CAREER_FIELDS = [
    ('q1_name', 'نام و نام خانوادگی'),
    ('q2_marital', 'سن / وضعیت تأهل'),
    ('q3_phone', 'شماره تماس'),
    ('q3_email', 'ایمیل'),
    ('how_heard', 'نحوه آشنایی با ما'),
    ('q4_job', 'شغل فعلی و زمینه فعالیت'),
    ('q5_city', 'شهر محل زندگی و کار'),
    ('q6_income', 'میزان درآمد تقریبی ماهانه'),
    ('q7_knot', 'بزرگ‌ترین گره کور شغلی'),
    ('q8_ideal', 'نتیجه ایده‌آل شش ماه بعد'),
    ('q9_actions', 'اقدامات قبلی'),
    ('q10_treatment', 'سابقه درمان'),
    ('q11_commitment', 'میزان تعهد'),
    ('q12_priority', 'اولویت سرمایه‌گذاری'),
]

ORG_FIELDS = [
    ('q1_org', 'نام سازمان / برند'),
    ('how_heard', 'نحوه آشنایی با ما'),
    ('q2_filler', 'نام و سمت تکمیل‌کننده'),
    ('q_contact_phone', 'شماره تماس'),
    ('q_contact_email', 'ایمیل'),
    ('q3_industry', 'زمینه فعالیت و صنعت'),
    ('q4_staff', 'تعداد پرسنل فعال'),
    ('q5_turnover', 'گردش مالی سالانه'),
    ('q6_budget', 'بودجه مصوب'),
    ('q7_focus', 'تمرکز اصلی کوچینگ'),
    ('q8_symptoms', 'چالش‌های رفتاری اصلی'),
    ('q9_root', 'ریشه چالش‌ها'),
    ('q10_kpi', 'شاخص کلیدی موفقیت'),
    ('q11_readiness', 'آمادگی هیئت‌مدیره'),
    ('q12_horizon', 'افق زمانی اجرا'),
]


# ── Career Intake ────────────────────────────────────────────────────────────

@intake_bp.route('/intake/career')
def career_intake_form():
    return render_template('intake_career.html')


@intake_bp.route('/intake/career', methods=['POST'])
@limiter.limit("10 per hour")
def submit_career_intake():
    data = request.get_json() or {}
    # Backward-compat: old single field q3_contact → split into phone/email
    if not data.get('q3_phone', '').strip() and data.get('q3_contact', '').strip():
        data['q3_phone'] = data['q3_contact'].strip()
    if not data.get('q3_email', '').strip() and data.get('q3_contact', '').strip() and '@' in data.get('q3_contact', ''):
        data['q3_email'] = data['q3_contact'].strip()
    missing = [label for field, label in CAREER_FIELDS if not str(data.get(field, '')).strip()]
    if missing:
        return jsonify({'error': 'missing_fields', 'missing': missing}), 400

    record = CareerIntake(**{field: str(data[field]).strip() for field, _ in CAREER_FIELDS})
    # Keep legacy column populated for old exports
    try:
        record.q3_contact = f"{record.q3_phone} / {record.q3_email}"
    except Exception:
        pass
    db.session.add(record)
    db.session.commit()

    answers = record.to_dict()

    def _bg_send():
        try:
            from email_service import send_career_intake_notification
            send_career_intake_notification(answers)
        except Exception as e:
            print(f"[EMAIL] Career intake notification error: {e}")

    threading.Thread(target=_bg_send, daemon=True).start()

    return jsonify({'success': True})


# ── Organizational Intake ────────────────────────────────────────────────────

@intake_bp.route('/intake/organizational')
def org_intake_form():
    return render_template('intake_org.html')


@intake_bp.route('/intake/organizational', methods=['POST'])
@limiter.limit("10 per hour")
def submit_org_intake():
    data = request.get_json() or {}
    missing = [label for field, label in ORG_FIELDS if not str(data.get(field, '')).strip()]
    if missing:
        return jsonify({'error': 'missing_fields', 'missing': missing}), 400

    record = OrgIntake(**{field: str(data[field]).strip() for field, _ in ORG_FIELDS})
    db.session.add(record)
    db.session.commit()

    answers = record.to_dict()

    def _bg_send():
        try:
            from email_service import send_org_intake_notification
            send_org_intake_notification(answers)
        except Exception as e:
            print(f"[EMAIL] Org intake notification error: {e}")

    threading.Thread(target=_bg_send, daemon=True).start()

    return jsonify({'success': True})
