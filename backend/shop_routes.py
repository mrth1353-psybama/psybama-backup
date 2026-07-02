import os
from flask import Blueprint, render_template, redirect, request, session, jsonify
from models import db, Product, Order, User
from models import iran_now
from payment import create_payment, verify_payment
from sms_service import send_sms

shop_bp = Blueprint('shop', __name__)

CARD_NUMBER = '6063731250080547'
CARD_OWNER  = 'محمد رضا تدریس حسنی'


@shop_bp.route('/')
def shop():
    products = Product.query.filter_by(is_active=True).all()
    return render_template('shop.html', products=products)


@shop_bp.route('/login')
def shop_login():
    if session.get('user_id'):
        next_url = request.args.get('next', '/shop')
        return redirect(next_url)
    next_url = request.args.get('next', '/shop')
    return render_template('shop_login.html', next_url=next_url)


@shop_bp.route('/checkout/<int:product_id>')
def checkout(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('checkout.html', product=product)


@shop_bp.route('/checkout/<int:product_id>/pay', methods=['POST'])
def pay(product_id):
    product = Product.query.get_or_404(product_id)
    method = request.form.get('payment_method')

    if method not in ('online', 'card'):
        return render_template('checkout.html', product=product, error='روش پرداخت نامعتبر است')

    order = Order(
        user_id=session.get('user_id'),
        product_id=product_id,
        payment_method=method,
        amount=product.price,
        status='pending_payment'
    )
    db.session.add(order)
    db.session.commit()

    if method == 'online':
        callback_url = request.host_url.rstrip('/') + f'/shop/verify/{order.id}'
        result = create_payment(product.price, product.name, callback_url)
        if result['success']:
            order.zarinpal_authority = result['authority']
            db.session.commit()
            return redirect(result['pay_url'])
        db.session.delete(order)
        db.session.commit()
        return render_template('checkout.html', product=product, error=result['error'])

    # card to card
    return redirect(f'/shop/card/{order.id}')


@shop_bp.route('/verify/<int:order_id>')
def verify(order_id):
    order = Order.query.get_or_404(order_id)
    authority = request.args.get('Authority', '')
    status    = request.args.get('Status', '')

    if status == 'OK' and authority and authority == order.zarinpal_authority:
        result = verify_payment(authority, order.amount)
        if result['success']:
            order.status   = 'pending_key'
            order.paid_at  = iran_now()
            db.session.commit()
            return render_template('order_success.html', order=order, ref_id=result['ref_id'], online=True)

    order.status = 'cancelled'
    db.session.commit()
    return render_template('order_result.html', order=order, success=False,
                           message='پرداخت ناموفق بود یا لغو شد.')


@shop_bp.route('/card/<int:order_id>')
def card_payment(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('payment_card.html', order=order,
                           card_number=CARD_NUMBER, card_owner=CARD_OWNER)


@shop_bp.route('/card/<int:order_id>/confirm', methods=['POST'])
def card_confirm(order_id):
    order = Order.query.get_or_404(order_id)
    # Mark as pending_payment (waiting admin to verify the SMS receipt)
    order.status = 'pending_payment'
    db.session.commit()
    return render_template('order_result.html', order=order, success=True,
                           message='درخواست شما ثبت شد. پس از بررسی رسید، کلید دسترسی از طریق پیامک ارسال می‌شود.')


@shop_bp.route('/orders')
def orders():
    if not session.get('user_id'):
        return redirect('/shop/login?next=/shop/orders')
    user_orders = (Order.query
                   .filter_by(user_id=session['user_id'])
                   .order_by(Order.created_at.desc())
                   .all())
    status_label = {
        'pending_payment': 'در انتظار تأیید پرداخت',
        'pending_key':     'پرداخت تأیید شد — در انتظار کلید',
        'completed':       'کلید ارسال شد ✓',
        'cancelled':       'لغو شده',
    }
    return render_template('orders.html', orders=user_orders, status_label=status_label)
