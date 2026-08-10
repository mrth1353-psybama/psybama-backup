import os
import sys
from pathlib import Path

# Make sure we find .env in the project root (one level up from backend/)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS

from models import db
from auth import login_required, create_or_update_otp, verify_otp
from sms_service import send_otp
from chat_handler import send_message, get_history
from admin_routes import admin_bp
from shop_routes import shop_bp
from rag_handler import load_knowledge_base


EBOOK_PRODUCT_NAME = 'کتاب مدیر هوشمند'
EBOOK_PRODUCT_LEGACY_NAME = 'ایبوک — عنوان جایگزین (به‌زودی نهایی می‌شود)'
EBOOK_PRODUCT_DESCRIPTION = 'کتاب مدیر هوشمند — راهنمای کاربردی برای مدیرانی که می‌خواهند هوشمندانه‌تر تصمیم بگیرند و تیمشان را مؤثرتر هدایت کنند.'
EBOOK_PRODUCT_PRICE = 220000

MBI_ITEMS = {
    'EE': [1, 2, 3, 6, 8, 13, 14, 16, 22],
    'DP': [5, 10, 11, 15, 21],
    'PA': [4, 7, 9, 12, 17, 18, 19, 20]
}

THRESHOLDS = {
    'EE': [('low', 0, 16), ('moderate', 17, 26), ('high', 27, 54)],
    'DP': [('low', 0, 6),  ('moderate', 7, 12),  ('high', 13, 30)],
    'PA': [('high', 0, 31), ('moderate', 32, 38), ('low', 39, 48)]
}

MBI_FEEDBACK = {
    ('high', 'high', 'high'):
        'نشانه‌های جدی فرسودگی شغلی در هر سه حوزه دارید. خستگی عاطفی شدید (نمره ۲۷ یا بالاتر) نشان می‌دهد از نظر روانی و جسمی به خاطر کار کاملاً تخلیه شده‌اید. مسخ شخصیت بالا (نمره ۱۳ یا بالاتر) حاکی از بی‌تفاوتی و بدبینی نسبت به مراجعان یا همکاران است. موفقیت فردی پایین (نمره ۳۱ یا کمتر) نشان‌دهنده احساس بی‌کفایتی و عدم اثربخشی در کار است. مشاوره با متخصص را حتماً در اولویت قرار دهید.',
    ('high', 'high', 'low'):
        'سطح فرسودگی شما بالا است. خستگی عاطفی (نمره ۲۷ یا بالاتر) و مسخ شخصیت (نمره ۱۳ یا بالاتر) هر دو نیاز به توجه دارند. از نظر روانی و جسمی به خاطر کار تخلیه شده‌اید و نسبت به مراجعان یا همکاران بی‌تفاوت و بدبین شده‌اید. با این حال احساس کفایت فردی شما در سطح قابل قبولی است.',
    ('high', 'moderate', 'low'):
        'خستگی عاطفی قابل توجهی دارید (نمره ۲۷ یا بالاتر). استراحت هدفمند و بازنگری در مرزهای کاری می‌تواند کمک کند. مسخ شخصیت در حد متوسط است و احساس کفایت فردی شما قابل قبول می‌باشد.',
    ('high', 'low', 'low'):
        'احساس فرسودگی عاطفی می‌کنید (نمره ۲۷ یا بالاتر). مرزبندی در کار و استراحت کافی را جدی بگیرید. مسخ شخصیت و موفقیت فردی شما در سطح نرمال است.',
    ('moderate', 'moderate', 'moderate'):
        'در مرحله میانی فرسودگی هستید. هر سه بعد در سطح متوسط قرار دارند. هنوز فرصت برای پیشگیری و بهبود وجود دارد. بازنگری در عادات کاری و مراقبت از سلامت روان را در اولویت قرار دهید.',
    ('moderate', 'high', 'low'):
        'مسخ شخصیت در شما نگران‌کننده است (نمره ۱۳ یا بالاتر). نسبت به مراجعان یا همکاران بی‌تفاوت و بدبین شده‌اید. خستگی عاطفی در حد متوسط است. با یک متخصص صحبت کنید.',
    ('low', 'low', 'low'):
        'خستگی عاطفی و مسخ شخصیت شما پایین است که نشانه خوبی است. اما موفقیت فردی شما پایین است (نمره ۳۱ یا کمتر) که نشان‌دهنده احساس بی‌کفایتی و عدم اثربخشی در کار است. روی شناسایی و تقویت نقاط قوت شغلی‌تان کار کنید.',
    ('low', 'low', 'high'):
        'خستگی عاطفی و مسخ شخصیت شما پایین است. اما احساس کفایت شغلی پایینی دارید (نمره ۳۱ یا کمتر). این می‌تواند نشانه نیاز به چالش‌های حرفه‌ای جدید یا بازتعریف نقش شغلی باشد.',
    ('high', 'low', 'high'):
        'خستگی عاطفی بالایی دارید (نمره ۲۷ یا بالاتر) اما مسخ شخصیت پایین و موفقیت فردی در سطح نرمال است. به نظر می‌رسد با وجود خستگی، همچنان ارتباط انسانی و احساس کارآمدی خود را حفظ کرده‌اید. به استراحت و مرزبندی بیشتر نیاز دارید.',
    ('high', 'moderate', 'high'):
        'خستگی عاطفی بالایی دارید (نمره ۲۷ یا بالاتر) و مسخ شخصیت در حد متوسط است. اما احساس موفقیت فردی شما پایین است (نمره ۳۱ یا کمتر). این ترکیب نشان می‌دهد با وجود خستگی، همچنان برای حفظ کیفیت کار خود تلاش می‌کنید اما احساس ناکارآمدی دارید.',
    ('moderate', 'low', 'low'):
        'خستگی عاطفی در حد متوسط است اما مسخ شخصیت و موفقیت فردی شما پایین است. احساس بی‌کفایتی در کار دارید. روی تقویت مهارت‌ها و بازتعریف اهداف شغلی کار کنید.',
    ('moderate', 'low', 'high'):
        'خستگی عاطفی متوسط و مسخ شخصیت پایین است. اما موفقیت فردی پایین (نمره ۳۱ یا کمتر) نشان‌دهنده احساس ناکارآمدی است. با وجود حفظ ارتباط انسانی، احساس می‌کنید در کارتان اثربخش نیستید.',
    ('low', 'moderate', 'low'):
        'خستگی عاطفی پایین است اما مسخ شخصیت در حد متوسط و موفقیت فردی پایین است. نیاز به تقویت احساس کفایت و کارآمدی در محیط کار دارید.',
    ('low', 'moderate', 'high'):
        'خستگی عاطفی پایین و مسخ شخصیت متوسط است. اما موفقیت فردی پایین (نمره ۳۱ یا کمتر) نیاز به توجه دارد. روی شناسایی دستاوردها و ارزش‌آفرینی در کار تمرکز کنید.',
    ('moderate', 'moderate', 'low'):
        'هر سه بعد در سطح متوسط تا پایین هستند. خستگی عاطفی و مسخ شخصیت در حد متوسط و موفقیت فردی پایین است. نیاز به برنامه جامع برای بهبود سلامت شغلی دارید.',
    ('moderate', 'moderate', 'high'):
        'خستگی عاطفی و مسخ شخصیت در حد متوسط است. موفقیت فردی پایین (نمره ۳۱ یا کمتر) نشان‌دهنده احساس ناکارآمدی است. با وجود تلاش، احساس می‌کنید به اندازه کافی مؤثر نیستید.',
}


# ── WAAQ (Work-related Acceptance and Action Questionnaire) ──────────────────

def score_waaq(responses):
    """Score the WAAQ (7 items, scale 1-7, all items direct scoring)."""
    assert len(responses) == 7, "WAAQ requires exactly 7 responses"

    items = [int(v) for v in responses]
    total = sum(items)

    if 7 <= total <= 26:
        level = 'low'
    elif 27 <= total <= 39:
        level = 'moderate'
    else:
        level = 'high'

    return {
        'items': items,
        'total_score': total,
        'level': level
    }


def classify(score, subscale):
    for level, lo, hi in THRESHOLDS[subscale]:
        if lo <= score <= hi:
            return level
    return 'high'


def score_mbi(responses):
    assert len(responses) == 22, "MBI requires exactly 22 responses"
    ee = sum(responses[i - 1] for i in MBI_ITEMS['EE'])
    dp = sum(responses[i - 1] for i in MBI_ITEMS['DP'])
    pa = sum(responses[i - 1] for i in MBI_ITEMS['PA'])

    ee_level = classify(ee, 'EE')
    dp_level = classify(dp, 'DP')
    pa_level = classify(pa, 'PA')

    key = (ee_level, dp_level, pa_level)
    feedback = MBI_FEEDBACK.get(key, 'نتایج پرسشنامه آماده است. برای تفسیر دقیق‌تر با یک متخصص مشورت کنید.')

    return {
        'ee': {'score': ee, 'max': 54, 'level': ee_level},
        'dp': {'score': dp, 'max': 30, 'level': dp_level},
        'pa': {'score': pa, 'max': 48, 'level': pa_level},
        'feedback': feedback
    }


def create_app():
    app = Flask(
        __name__,
        template_folder='../frontend/templates',
        static_folder='../frontend/static'
    )

    app.secret_key = os.getenv('SECRET_KEY', 'dev-insecure-change-in-production')

    # Resolve database path relative to project root (parent of backend/)
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    db_path = (data_dir / 'psybama.db').as_posix()
    default_db = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', default_db)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_AS_ASCII'] = False

    CORS(app, resources={r'/api/*': {'origins': '*'}}, supports_credentials=True)

    db.init_app(app)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(shop_bp, url_prefix='/shop')

    # ── Page routes ──────────────────────────────────────────────────────────

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/chat')
    def chat():
        return render_template('chat.html')

    @app.route('/course/zendegi-hooshmandane')
    def course_zendegi_hooshmandane():
        from models import Product
        product = Product.query.filter_by(name='دوره زندگیِ هوشمندانه').first()
        return render_template('course_zendegi_hooshmandane.html', product_id=product.id if product else 0)

    @app.route('/course/raze-arzeshmandi')
    def course_raze_arzeshmandi():
        from models import Product
        product = Product.query.filter_by(name='دوره راز ارزشمندی').first()
        return render_template('course_raze_arzeshmandi.html', product_id=product.id if product else 0)

    @app.route('/services')
    def services():
        return render_template('services.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'POST':
            name = (request.form.get('name') or '').strip()
            phone = (request.form.get('phone') or '').strip()
            message = (request.form.get('message') or '').strip()
            if name and phone:
                from models import ContactRequest
                cr = ContactRequest(name=name, phone=phone, message=message)
                db.session.add(cr)
                db.session.commit()
                try:
                    from email_service import send_contact_notification
                    result = send_contact_notification(name, phone, message)
                    if not result.get('success'):
                        print(f"[EMAIL NOTIFICATION] Failed: {result.get('error')}")
                except Exception as e:
                    print(f"[EMAIL NOTIFICATION] Error: {e}")
                return render_template('contact.html', success=True)
            return render_template('contact.html', error=True)
        return render_template('contact.html')

    @app.route('/assessment')
    def assessment():
        from models import Product
        ebook_product = Product.query.filter_by(name=EBOOK_PRODUCT_NAME).first()
        return render_template('assessment.html', ebook_product=ebook_product)

    @app.route('/waaq')
    def waaq():
        from models import Product
        ebook_product = Product.query.filter_by(name=EBOOK_PRODUCT_NAME).first()
        return render_template('waaq.html', ebook_product=ebook_product)

    # ── Auth API ──────────────────────────────────────────────────────────────

    @app.route('/api/auth/request-otp', methods=['POST'])
    def request_otp():
        data = request.get_json()
        phone = (data or {}).get('phone_number', '').strip()

        if not phone or len(phone) < 10:
            return jsonify({'error': 'invalid_phone', 'message': 'شماره موبایل معتبر نیست'}), 400

        user, otp = create_or_update_otp(phone)
        result = send_otp(phone, otp)

        return jsonify({
            'success': True,
            'message': 'کد تأیید ارسال شد',
            'display_otp': result.get('display_otp'),
            'mode': result.get('mode')
        })

    @app.route('/api/auth/verify-otp', methods=['POST'])
    def verify_otp_route():
        data = request.get_json()
        phone = (data or {}).get('phone_number', '').strip()
        code = (data or {}).get('otp_code', '').strip()

        if not phone or not code:
            return jsonify({'error': 'missing_fields', 'message': 'شماره و کد الزامی است'}), 400

        ok, reason = verify_otp(phone, code)
        if not ok:
            messages = {
                'user_not_found': 'ابتدا کد را دریافت کنید',
                'no_otp_issued': 'ابتدا کد را دریافت کنید',
                'otp_expired': 'کد منقضی شده است. کد جدید دریافت کنید',
                'otp_mismatch': 'کد وارد شده اشتباه است'
            }
            return jsonify({'error': reason, 'message': messages.get(reason, 'خطا در تأیید کد')}), 400

        from models import User
        user = User.query.filter_by(phone_number=phone).first()
        session['user_id'] = user.id
        session['phone_number'] = phone

        return jsonify({'success': True, 'message': 'ورود موفق', 'user_id': user.id})

    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        session.pop('user_id', None)
        session.pop('phone_number', None)
        return jsonify({'success': True})

    @app.route('/api/auth/status')
    def auth_status():
        return jsonify({
            'logged_in': 'user_id' in session,
            'phone_number': session.get('phone_number')
        })

    # ── Chat API ──────────────────────────────────────────────────────────────

    @app.route('/api/chat/message', methods=['POST'])
    @login_required
    def chat_message():
        data = request.get_json()
        text = (data or {}).get('message', '').strip()
        conv_id = (data or {}).get('conversation_id')

        if not text:
            return jsonify({'error': 'empty_message', 'message': 'پیام خالی است'}), 400

        result = send_message(
            user_id=session['user_id'],
            user_text=text,
            conversation_id=conv_id
        )

        if 'error' in result:
            return jsonify(result), 500

        return jsonify(result)

    @app.route('/api/chat/new-conversation', methods=['POST'])
    @login_required
    def new_conversation():
        import uuid
        from models import Conversation
        conv = Conversation(user_id=session['user_id'], session_id=uuid.uuid4().hex)
        db.session.add(conv)
        db.session.commit()
        return jsonify({'conversation_id': conv.id})

    @app.route('/api/chat/history/<int:conv_id>')
    @login_required
    def chat_history(conv_id):
        history = get_history(session['user_id'], conv_id)
        return jsonify({'messages': history})

    @app.route('/api/chat/conversations/<int:conv_id>', methods=['DELETE'])
    @login_required
    def hide_conversation(conv_id):
        from models import Conversation
        conv = Conversation.query.filter_by(id=conv_id, user_id=session['user_id']).first()
        if not conv:
            return jsonify({'error': 'not_found'}), 404
        conv.hidden_by_user = True
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/api/chat/conversations')
    @login_required
    def user_conversations():
        from models import Conversation, Message
        convs = (Conversation.query
                 .filter_by(user_id=session['user_id'], hidden_by_user=False)
                 .order_by(Conversation.started_at.desc())
                 .limit(30)
                 .all())
        result = []
        for c in convs:
            first_msg = (Message.query
                         .filter_by(conversation_id=c.id, role='user')
                         .order_by(Message.timestamp)
                         .first())
            if first_msg:
                preview = first_msg.content[:40] + ('…' if len(first_msg.content) > 40 else '')
            else:
                preview = 'گفتگو'
            msg_count = Message.query.filter_by(conversation_id=c.id).count()
            result.append({
                'id': c.id,
                'started_at': c.started_at.isoformat() if c.started_at else None,
                'preview': preview,
                'message_count': msg_count
            })
        return jsonify({'conversations': result})

    # ── FAQ Widget API ────────────────────────────────────────────────────────

    @app.route('/api/faq/message', methods=['POST'])
    def faq_message():
        from faq_handler import get_faq_reply

        data = request.get_json()
        text = (data or {}).get('message', '').strip()

        if not text:
            return jsonify({'error': 'empty_message', 'message': 'پیام خالی است'}), 400
        if len(text) > 300:
            return jsonify({'error': 'message_too_long', 'message': 'پیام خیلی طولانی است'}), 400

        try:
            reply = get_faq_reply(text)
        except Exception as e:
            return jsonify({'error': f'ai_error: {e}'}), 500

        return jsonify({'reply': reply})

    # ── Assessment API ────────────────────────────────────────────────────────

    @app.route('/api/assessment/lead', methods=['POST'])
    def submit_assessment_lead():
        import re
        data = request.get_json()
        name = ((data or {}).get('name') or '').strip()
        email = ((data or {}).get('email') or '').strip()
        phone = ((data or {}).get('phone') or '').strip()

        if not name:
            return jsonify({'error': 'invalid_name', 'message': 'نام و نام خانوادگی الزامی است'}), 400
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({'error': 'invalid_email', 'message': 'ایمیل معتبر نیست'}), 400
        if not re.match(r'^09\d{9}$', phone):
            return jsonify({'error': 'invalid_phone', 'message': 'شماره موبایل معتبر نیست'}), 400

        from models import AssessmentLead
        lead = AssessmentLead(name=name, email=email, phone=phone)
        db.session.add(lead)
        db.session.commit()

        session['assessment_lead_id'] = lead.id

        return jsonify({'success': True})

    @app.route('/api/assessment/submit', methods=['POST'])
    def submit_assessment():
        data = request.get_json()
        responses = (data or {}).get('responses', [])

        if len(responses) != 22:
            return jsonify({'error': 'invalid_responses', 'message': 'باید ۲۲ پاسخ ارسال شود'}), 400

        try:
            responses = [int(r) for r in responses]
            assert all(0 <= r <= 6 for r in responses)
        except (ValueError, AssertionError):
            return jsonify({'error': 'invalid_values', 'message': 'مقادیر باید بین ۰ تا ۶ باشند'}), 400

        scores = score_mbi(responses)

        from models import Assessment
        user_id = session.get('user_id')
        lead_id = session.get('assessment_lead_id')
        assessment = Assessment(
            user_id=user_id,
            lead_id=lead_id,
            emotional_exhaustion=scores['ee']['score'],
            depersonalization=scores['dp']['score'],
            personal_accomplishment=scores['pa']['score'],
            ee_level=scores['ee']['level'],
            dp_level=scores['dp']['level'],
            pa_level=scores['pa']['level']
        )
        db.session.add(assessment)
        db.session.commit()

        return jsonify({'success': True, 'scores': scores})

    # ── WAAQ API ──────────────────────────────────────────────────────────────

    @app.route('/api/waaq/submit', methods=['POST'])
    def submit_waaq():
        data = request.get_json()
        responses = (data or {}).get('responses', [])

        if len(responses) != 7:
            return jsonify({'error': 'invalid_responses', 'message': 'باید ۷ پاسخ ارسال شود'}), 400

        try:
            responses = [int(r) for r in responses]
            assert all(1 <= r <= 7 for r in responses)
        except (ValueError, AssertionError):
            return jsonify({'error': 'invalid_values', 'message': 'مقادیر باید بین ۱ تا ۷ باشند'}), 400

        scores = score_waaq(responses)

        from models import WaaqAssessment
        user_id = session.get('user_id')
        lead_id = session.get('assessment_lead_id')
        items = scores['items']
        assessment = WaaqAssessment(
            user_id=user_id,
            lead_id=lead_id,
            item1=items[0],
            item2=items[1],
            item3=items[2],
            item4=items[3],
            item5=items[4],
            item6=items[5],
            item7=items[6],
            total_score=scores['total_score'],
            level=scores['level']
        )
        db.session.add(assessment)
        db.session.commit()

        return jsonify({'success': True, 'scores': scores})

    # ── DB Init ───────────────────────────────────────────────────────────────

    with app.app_context():
        db.create_all()
        # Migration: add hidden_by_user column if it doesn't exist yet
        try:
            from sqlalchemy import text
            db.session.execute(text(
                'ALTER TABLE conversations ADD COLUMN hidden_by_user BOOLEAN NOT NULL DEFAULT 0'
            ))
            db.session.commit()
            print('[DB] Migration: added hidden_by_user column')
        except Exception:
            db.session.rollback()

        # Migration: allow guest orders (user_id nullable)
        try:
            from sqlalchemy import text
            db.session.execute(text(
                'ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL'
            ))
            db.session.commit()
            print('[DB] Migration: orders.user_id is now nullable')
        except Exception:
            db.session.rollback()

        # Migration: add lead_id column to assessments if it doesn't exist yet
        try:
            from sqlalchemy import text
            db.session.execute(text(
                'ALTER TABLE assessments ADD COLUMN lead_id INTEGER'
            ))
            db.session.commit()
            print('[DB] Migration: added lead_id column to assessments')
        except Exception:
            db.session.rollback()

        # Seed placeholder products if none exist
        from models import Product
        if Product.query.count() == 0:
            placeholders = [
                Product(name='محصول آموزشی ۱', description='توضیحات محصول اول را اینجا وارد کنید.', price=490000),
                Product(name='محصول آموزشی ۲', description='توضیحات محصول دوم را اینجا وارد کنید.', price=790000),
                Product(name='محصول آموزشی ۳', description='توضیحات محصول سوم را اینجا وارد کنید.', price=990000),
            ]
            db.session.add_all(placeholders)
            db.session.commit()
            print('[DB] Seeded 3 placeholder products')

        # Seed "دوره زندگیِ هوشمندانه" product if not exists (update price if exists)
        from models import Product
        zendegi_product = Product.query.filter_by(name='دوره زندگیِ هوشمندانه').first()
        if not zendegi_product:
            zendegi_product = Product(
                name='دوره زندگیِ هوشمندانه',
                description='دوره غیرحضوری زندگیِ هوشمندانه — گام‌های حساب‌شده تا خلق دستاورد. مدرس: دکتر مرضیه فیضی',
                price=28000000
            )
            db.session.add(zendegi_product)
            db.session.commit()
            print('[DB] Seeded "دوره زندگیِ هوشمندانه" product')
        elif zendegi_product.price != 28000000:
            zendegi_product.price = 28000000
            db.session.commit()
            print('[DB] Updated "دوره زندگیِ هوشمندانه" price to 28,000,000')

        # Seed "دوره راز ارزشمندی" product if not exists (update price if exists)
        raze_product = Product.query.filter_by(name='دوره راز ارزشمندی').first()
        if not raze_product:
            raze_product = Product(
                name='دوره راز ارزشمندی',
                description='دوره راز ارزشمندی — با تقویت عزت‌نفس، از اسارت سرزنش‌ها و تردیدها رها شوید. مدرس: مرضیه فیضی',
                price=3800000
            )
            db.session.add(raze_product)
            db.session.commit()
            print('[DB] Seeded "دوره راز ارزشمندی" product')
        elif raze_product.price != 3800000:
            raze_product.price = 3800000
            db.session.commit()
            print('[DB] Updated "دوره راز ارزشمندی" price to 3,800,000')

        # Sync "کتاب مدیر هوشمند" ebook product (rename legacy placeholder if present)
        ebook_product = Product.query.filter_by(name=EBOOK_PRODUCT_NAME).first()
        if ebook_product:
            changed = False
            if ebook_product.description != EBOOK_PRODUCT_DESCRIPTION:
                ebook_product.description = EBOOK_PRODUCT_DESCRIPTION
                changed = True
            if ebook_product.price != EBOOK_PRODUCT_PRICE:
                ebook_product.price = EBOOK_PRODUCT_PRICE
                changed = True
            if changed:
                db.session.commit()
        else:
            legacy = Product.query.filter_by(name=EBOOK_PRODUCT_LEGACY_NAME).first()
            if legacy:
                legacy.name = EBOOK_PRODUCT_NAME
                legacy.description = EBOOK_PRODUCT_DESCRIPTION
                legacy.price = EBOOK_PRODUCT_PRICE
                db.session.commit()
                print('[DB] Renamed legacy ebook product to "کتاب مدیر هوشمند"')
            else:
                ebook_product = Product(
                    name=EBOOK_PRODUCT_NAME,
                    description=EBOOK_PRODUCT_DESCRIPTION,
                    price=EBOOK_PRODUCT_PRICE
                )
                db.session.add(ebook_product)
                db.session.commit()
                print('[DB] Seeded "کتاب مدیر هوشمند" ebook product')

        # Deactivate any remaining legacy placeholder so it disappears from the shop
        legacy_placeholder = Product.query.filter_by(name=EBOOK_PRODUCT_LEGACY_NAME).first()
        if legacy_placeholder and legacy_placeholder.is_active:
            legacy_placeholder.is_active = False
            db.session.commit()
            print('[DB] Deactivated legacy ebook placeholder product')

        load_knowledge_base()

    return app


app = create_app()

if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print("\n" + "=" * 55)
    print("  Psybama / سای‌باما - Ready!")
    print("  http://localhost:5000")
    print("  Admin: http://localhost:5000/admin/")
    print("=" * 55 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
