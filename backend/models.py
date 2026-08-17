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
    created_at = db.Column(db.DateTime, default=iran_now)

    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'is_verified': self.is_verified,
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
    orders = db.relationship('Order', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'is_active': self.is_active
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'online' or 'card'
    status = db.Column(db.String(20), default='pending_payment')
    # pending_payment | pending_key | completed | cancelled
    amount = db.Column(db.Integer, nullable=False)  # Tomans
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
            'payment_method': self.payment_method,
            'status': self.status,
            'amount': self.amount,
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
