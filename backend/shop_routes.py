import os
from flask import Blueprint, render_template, redirect, request, session, jsonify
from models import db, Product, Order, User
from models import iran_now
from payment import create_payment, verify_payment
from sms_service import send_sms

shop_bp = Blueprint('shop', __name__)

CARD_NUMBER = '6104337935480440'
CARD_SHEBA  = 'IR8701200000001524891721'
CARD_OWNER  = 'مرضیه فیضی'
CONTACT_PHONE = '09910216842'


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

    if method == 'online':
        return redirect(f'/shop/checkout/{product_id}/online')

    order = Order(
        user_id=session.get('user_id'),
        product_id=product_id,
        payment_method='card',
        amount=product.price,
        status='pending_payment'
    )
    db.session.add(order)
    db.session.commit()
    return redirect(f'/shop/card/{order.id}')


@shop_bp.route('/checkout/<int:product_id>/online', methods=['GET'])
def online_form(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('payment_online.html', product=product)


@shop_bp.route('/checkout/<int:product_id>/online', methods=['POST'])
def online_pay(product_id):
    product = Product.query.get_or_404(product_id)

    full_name = (request.form.get('full_name') or '').strip()
    phone = (request.form.get('phone') or '').strip()
    address = (request.form.get('address') or '').strip()
    postal_code = (request.form.get('postal_code') or '').strip()

    if not full_name or not phone or not address or not postal_code:
        return render_template('payment_online.html', product=product,
                               error='لطفاً تمام فیلدها را پر کنید.')

    order = Order(
        user_id=session.get('user_id'),
        product_id=product_id,
        payment_method='online',
        amount=product.price,
        customer_name=full_name,
        customer_phone=phone,
        customer_address=address,
        customer_postal_code=postal_code,
        status='pending_payment'
    )
    db.session.add(order)
    db.session.commit()

    site_url = os.getenv('SITE_URL', request.host_url.rstrip('/'))
    callback_url = f'{site_url}/shop/verify/{order.id}'

    result = create_payment(
        amount_tomans=product.price,
        description=f'خرید {product.name} - {full_name}',
        callback_url=callback_url
    )

    if result['success']:
        order.zarinpal_authority = result['authority']
        db.session.commit()
        return redirect(result['pay_url'])

    db.session.delete(order)
    db.session.commit()
    return render_template('payment_online.html', product=product,
                           error=result.get('error', 'خطا در اتصال به درگاه پرداخت.'))


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
            return render_template('order_result.html', order=order, success=True,
                                   message=f'پرداخت موفق بود. کد پیگیری: {result["ref_id"]}')

    order.status = 'cancelled'
    db.session.commit()
    return render_template('order_result.html', order=order, success=False,
                           message='پرداخت ناموفق بود یا لغو شد.')


@shop_bp.route('/card/<int:order_id>')
def card_payment(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('payment_card.html', order=order,
                           card_number=CARD_NUMBER, card_sheba=CARD_SHEBA,
                           card_owner=CARD_OWNER, contact_phone=CONTACT_PHONE)


@shop_bp.route('/card/<int:order_id>/confirm', methods=['POST'])
def card_confirm(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'pending_payment'
    db.session.commit()
    return render_template('order_result.html', order=order, success=True,
                           message='از خرید شما متشکریم. پس از ارسال فیش واریزی با شما تماس می‌گیریم و لایسنس محصول در اختیار شما قرار می‌گیرد.')


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
