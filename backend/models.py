from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta

db = SQLAlchemy()

def iran_now():
    return datetime.now(timezone(timedelta(hours=3, minutes=30))).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    full_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=iran_now)

    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'is_verified': self.is_verified,
            'full_name': self.full_name,
            'email': self.email,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'conversation_count': len(self.conversations)
        }


class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(64), unique=True, nullable=False)
    started_at = db.Column(db.DateTime, default=iran_now)
    hidden_by_user = db.Column(db.Boolean, default=False, nullable=False, server_default='0')

    messages = db.relationship(
        'Message', backref='conversation', lazy=True,
        order_by='Message.timestamp', cascade='all, delete-orphan'
    )

    def to_dict(self, include_messages=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'message_count': len(self.messages)
        }
        if include_messages:
            data['messages'] = [m.to_dict() for m in self.messages]
        return data


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=iran_now, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class ContactRequest(db.Model):
    __tablename__ = 'contact_requests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=iran_now)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_read': self.is_read
        }


class AssessmentLead(db.Model):
    __tablename__ = 'assessment_leads'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=iran_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Integer, nullable=False)  # Tomans
    is_active = db.Column(db.Boolean, default=True)
    delivery_type = db.Column(db.String(20), default='digital',
                              nullable=False, server_default='digital')
    orders = db.relationship('Order', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'is_active': self.is_active,
            'delivery_type': self.delivery_type
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'online' or 'card'
    status = db.Column(db.String(20), default='pending_payment')
    # pending_payment | pending_key | completed | cancelled
    amount = db.Column(db.Integer, nullable=False)  # Tomans (پس از تخفیف)
    discount_code = db.Column(db.String(50), nullable=True)
    discount_amount = db.Column(db.Integer, nullable=True)  # Tomans
    zarinpal_authority = db.Column(db.String(100), nullable=True)
    customer_name = db.Column(db.String(200), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_address = db.Column(db.Text, nullable=True)
    customer_postal_code = db.Column(db.String(10), nullable=True)
    spotplayer_key = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=iran_now)
    paid_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='orders', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone_number': self.user.phone_number if self.user else '—',
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '—',
            'delivery_type': self.product.delivery_type if self.product else 'digital',
            'payment_method': self.payment_method,
            'status': self.status,
            'amount': self.amount,
            'discount_code': self.discount_code,
            'discount_amount': self.discount_amount,
            'spotplayer_key': self.spotplayer_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('assessment_leads.id'), nullable=True)

    # MBI subscale raw scores
    emotional_exhaustion = db.Column(db.Float, nullable=False)      # EE: 0-54
    depersonalization = db.Column(db.Float, nullable=False)         # DP: 0-30
    personal_accomplishment = db.Column(db.Float, nullable=False)   # PA: 0-48

    # Severity levels: 'low', 'moderate', 'high'
    ee_level = db.Column(db.String(10))
    dp_level = db.Column(db.String(10))
    pa_level = db.Column(db.String(10))

    completed_at = db.Column(db.DateTime, default=iran_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lead_id': self.lead_id,
            'emotional_exhaustion': self.emotional_exhaustion,
            'depersonalization': self.depersonalization,
            'personal_accomplishment': self.personal_accomplishment,
            'ee_level': self.ee_level,
            'dp_level': self.dp_level,
            'pa_level': self.pa_level,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class WaaqAssessment(db.Model):
    __tablename__ = 'waaq_assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('assessment_leads.id'), nullable=True)

    user = db.relationship('User', lazy=True)
    lead = db.relationship('AssessmentLead', lazy=True)

    # Individual item scores (1-7 each, after reverse-scoring)
    item1 = db.Column(db.Integer, nullable=False)
    item2 = db.Column(db.Integer, nullable=False)
    item3 = db.Column(db.Integer, nullable=False)
    item4 = db.Column(db.Integer, nullable=False)
    item5 = db.Column(db.Integer, nullable=False)
    item6 = db.Column(db.Integer, nullable=False)
    item7 = db.Column(db.Integer, nullable=False)

    # Total score (7-49)
    total_score = db.Column(db.Integer, nullable=False)

    # Level: 'low', 'moderate', 'high'
    level = db.Column(db.String(10))

    completed_at = db.Column(db.DateTime, default=iran_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lead_id': self.lead_id,
            'item1': self.item1,
            'item2': self.item2,
            'item3': self.item3,
            'item4': self.item4,
            'item5': self.item5,
            'item6': self.item6,
            'item7': self.item7,
            'total_score': self.total_score,
            'level': self.level,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class CareerKnotAssessment(db.Model):
    __tablename__ = 'career_knot_assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('assessment_leads.id'), nullable=True)

    user = db.relationship('User', lazy=True)
    lead = db.relationship('AssessmentLead', lazy=True)

    # Individual item answers (1=الف/a, 2=ب/b, 3=ج/c, 4=د/d)
    item1 = db.Column(db.Integer, nullable=False)
    item2 = db.Column(db.Integer, nullable=False)
    item3 = db.Column(db.Integer, nullable=False)
    item4 = db.Column(db.Integer, nullable=False)
    item5 = db.Column(db.Integer, nullable=False)
    item6 = db.Column(db.Integer, nullable=False)
    item7 = db.Column(db.Integer, nullable=False)
    item8 = db.Column(db.Integer, nullable=False)

    # Optional per-item free-text comments stored as JSON array
    comments = db.Column(db.Text, nullable=True)

    # Counts of each chosen letter across all items
    count_a = db.Column(db.Integer, nullable=False)
    count_b = db.Column(db.Integer, nullable=False)
    count_c = db.Column(db.Integer, nullable=False)
    count_d = db.Column(db.Integer, nullable=False)

    # Total score T = max(count_a, count_b, count_c, count_d)
    total_score = db.Column(db.Integer, nullable=False)

    # Interpretation section: 1, 2 or 3
    section = db.Column(db.Integer, nullable=False)

    # Profile code: a|b|c|d (section 1), ab|ac|ad|bc|bd|cd (section 2), mixed (section 3)
    profile_code = db.Column(db.String(10), nullable=False)
    profile_title = db.Column(db.String(100), nullable=False)

    completed_at = db.Column(db.DateTime, default=iran_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lead_id': self.lead_id,
            'item1': self.item1,
            'item2': self.item2,
            'item3': self.item3,
            'item4': self.item4,
            'item5': self.item5,
            'item6': self.item6,
            'item7': self.item7,
            'item8': self.item8,
            'comments': self.comments,
            'count_a': self.count_a,
            'count_b': self.count_b,
            'count_c': self.count_c,
            'count_d': self.count_d,
            'total_score': self.total_score,
            'section': self.section,
            'profile_code': self.profile_code,
            'profile_title': self.profile_title,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class WebinarRegistration(db.Model):
    __tablename__ = 'webinar_registrations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    webinar_title = db.Column(db.String(200), nullable=False)
    webinar_date = db.Column(db.String(100), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('assessment_leads.id'), nullable=True)
    sms_sent = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=iran_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'webinar_title': self.webinar_title,
            'webinar_date': self.webinar_date,
            'lead_id': self.lead_id,
            'sms_sent': self.sms_sent,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CareerIntake(db.Model):
    __tablename__ = 'career_intakes'

    id = db.Column(db.Integer, primary_key=True)
    q1_name = db.Column(db.String(150), nullable=False)
    q2_marital = db.Column(db.String(100), nullable=False)
    q3_contact = db.Column(db.String(200), nullable=True)
    q3_phone = db.Column(db.String(50), nullable=True)
    q3_email = db.Column(db.String(150), nullable=True)
    q4_job = db.Column(db.String(200), nullable=False)
    q5_city = db.Column(db.String(100), nullable=False)
    q6_income = db.Column(db.String(60), nullable=False)
    q7_knot = db.Column(db.Text, nullable=False)
    q8_ideal = db.Column(db.Text, nullable=False)
    q9_actions = db.Column(db.Text, nullable=False)
    q10_treatment = db.Column(db.String(80), nullable=False)
    q11_commitment = db.Column(db.String(10), nullable=False)
    q12_priority = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=iran_now)

    def to_dict(self):
        phone = self.q3_phone or ''
        email = self.q3_email or ''
        if not phone and not email and self.q3_contact:
            phone = self.q3_contact
        return {
            'id': self.id,
            'answers': [
                {'q': '۱. نام و نام خانوادگی', 'a': self.q1_name},
                {'q': '۲. سن / وضعیت تأهل', 'a': self.q2_marital},
                {'q': '۳. شماره تماس', 'a': phone},
                {'q': '۴. ایمیل', 'a': email},
                {'q': '۵. شغل فعلی و زمینه فعالیت', 'a': self.q4_job},
                {'q': '۶. شهر محل زندگی و کار', 'a': self.q5_city},
                {'q': '۷. میزان درآمد تقریبی ماهانه', 'a': self.q6_income},
                {'q': '۸. بزرگ‌ترین گره کور یا چالش شغلی', 'a': self.q7_knot},
                {'q': '۹. شش ماه بعد به نتیجه ایده‌آل — شاخص موفقیت', 'a': self.q8_ideal},
                {'q': '۱۰. اقدامات قبلی و نتیجه', 'a': self.q9_actions},
                {'q': '۱۱. سابقه درمان روان‌پزشکی/روان‌درمانی', 'a': self.q10_treatment},
                {'q': '۱۲. میزان تعهد و انرژی (۱ تا ۱۰)', 'a': self.q11_commitment},
                {'q': '۱۳. اولویت سرمایه‌گذاری روی رشد شغلی', 'a': self.q12_priority},
            ],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class OrgIntake(db.Model):
    __tablename__ = 'org_intakes'

    id = db.Column(db.Integer, primary_key=True)
    q1_org = db.Column(db.String(200), nullable=False)
    q2_filler = db.Column(db.String(200), nullable=False)
    q_contact_phone = db.Column(db.String(50), nullable=True)
    q_contact_email = db.Column(db.String(150), nullable=True)
    q3_industry = db.Column(db.String(200), nullable=False)
    q4_staff = db.Column(db.String(80), nullable=False)
    q5_turnover = db.Column(db.String(200), nullable=False)
    q6_budget = db.Column(db.String(200), nullable=False)
    q7_focus = db.Column(db.String(120), nullable=False)
    q8_symptoms = db.Column(db.Text, nullable=False)
    q9_root = db.Column(db.Text, nullable=False)
    q10_kpi = db.Column(db.Text, nullable=False)
    q11_readiness = db.Column(db.String(10), nullable=False)
    q12_horizon = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=iran_now)

    def to_dict(self):
        return {
            'id': self.id,
            'answers': [
                {'q': '۱. نام سازمان / برند', 'a': self.q1_org},
                {'q': '۲. نام و سمت تکمیل‌کننده فرم', 'a': self.q2_filler},
                {'q': '۳. شماره تماس', 'a': self.q_contact_phone or ''},
                {'q': '۴. ایمیل', 'a': self.q_contact_email or ''},
                {'q': '۵. زمینه فعالیت و صنعت', 'a': self.q3_industry},
                {'q': '۶. تعداد پرسنل فعال', 'a': self.q4_staff},
                {'q': '۷. میزان گردش مالی سالانه', 'a': self.q5_turnover},
                {'q': '۸. بودجه مصوب توسعه منابع انسانی', 'a': self.q6_budget},
                {'q': '۹. تمرکز اصلی فرآیند کوچینگ', 'a': self.q7_focus},
                {'q': '۱۰. سه نشانه / چالش رفتاری اصلی', 'a': self.q8_symptoms},
                {'q': '۱۱. ریشه چالش‌ها و موانع رفع آن', 'a': self.q9_root},
                {'q': '۱۲. شاخص کلیدی موفقیت (KPI)', 'a': self.q10_kpi},
                {'q': '۱۳. میزان آمادگی هیئت‌مدیره (۱ تا ۵)', 'a': self.q11_readiness},
                {'q': '۱۴. افق زمانی اجرای برنامه', 'a': self.q12_horizon},
            ],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
