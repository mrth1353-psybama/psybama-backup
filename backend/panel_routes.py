from flask import Blueprint, render_template, session, jsonify, request
from auth import login_required
from models import db, User, Order, Product
from models import iran_now

panel_bp = Blueprint('panel', __name__)

STATUS_LABEL = {
    'pending_payment': 'در انتظار پرداخت',
    'pending_key':     'پرداخت تایید شد — در انتظار ارسال',
    'completed':       'تکمیل شد ✓',
    'cancelled':       'لغو شده',
}
METHOD_LABEL = {'online': 'آنلاین', 'card': 'کارت به کارت'}


@panel_bp.route('/')
@login_required
def panel_home():
    return render_template('panel.html', status_label=STATUS_LABEL)


@panel_bp.route('/orders')
@login_required
def panel_orders():
    return render_template('panel.html', status_label=STATUS_LABEL)


@panel_bp.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    user = User.query.get_or_404(session['user_id'])
    return jsonify({'success': True, 'user': user.to_dict()})


@panel_bp.route('/api/profile', methods=['POST'])
@login_required
def update_profile():
    user = User.query.get_or_404(session['user_id'])
    data = request.get_json() or {}

    full_name = (data.get('full_name') or '').strip()
    email = (data.get('email') or '').strip()

    if full_name:
        if len(full_name) > 100:
            return jsonify({'error': 'invalid_name', 'message': 'نام بیش از حد طولانی است'}), 400
        user.full_name = full_name

    if email:
        import re
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return jsonify({'error': 'invalid_email', 'message': 'ایمیل معتبر نیست'}), 400
        user.email = email

    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()})


@panel_bp.route('/api/orders', methods=['GET'])
@login_required
def get_completed_orders():
    """سفارشات پرداخت‌شده کاربر (pending_key و completed) — فقط متعلق به همین کاربر.
    وضعیت pending_key یعنی پرداخت تایید شده و در انتظار ارسال (محصول فیزیکی)."""
    orders = (Order.query
              .filter(Order.user_id == session['user_id'],
                      Order.status.in_(['pending_key', 'completed']))
              .order_by(Order.created_at.desc())
              .all())

    result = []
    for o in orders:
        result.append({
            'id': o.id,
            'product_id': o.product_id,
            'product_name': o.product.name if o.product else '—',
            'amount': o.amount,
            'payment_method': o.payment_method,
            'method_label': METHOD_LABEL.get(o.payment_method, o.payment_method),
            'status': o.status,
            'status_label': STATUS_LABEL.get(o.status, o.status),
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'completed_at': o.completed_at.isoformat() if o.completed_at else None,
        })

    return jsonify({'success': True, 'orders': result})
