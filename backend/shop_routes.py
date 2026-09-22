import os
from urllib.parse import quote

from flask import Blueprint, render_template, redirect, request, session, jsonify
from models import db, Product, Order, User
from models import iran_now
from payment import create_payment, verify_payment
from sms_service import send_sms
from discounts import evaluate_discount

shop_bp = Blueprint('shop', __name__)

CARD_NUMBER = '6104337935480440'
CARD_SHEBA  = 'IR8701200000001524891721'
CARD_OWNER  = 'مرضیه فیضی'
CONTACT_PHONE = '09910216842'

# هزینه ارسال کتاب فیزیکی (تومان) — فقط در جریان پاپ‌آپ اعمال می‌شود
SHIPPING_COST = 150000

# قیمت نهایی مسیر پاپ‌آپ (کتاب + هزینه ارسال) — در تمام مراحل و درگاه پرداخت همین عدد است
POPUP_FINAL_PRICE = 350000

# کد تخفیف اختصاصی پاپ‌آپ کتاب مدیر هوشمند (۵۰٪ + ارسال)
POPUP_PROMO_CODE = 'KNOT50'


def compute_order_amount(product, discount):
    """مبلغ نهایی سفارش = قیمت پس از تخفیف + هزینه ارسال.

    هزینه ارسال فقط زمانی اعمال می‌شود که کد تخفیفِ پاپ‌آپ (KNOT50) استفاده شده باشد،
    نه در سایر خریدهای محصول فیزیکی.
    """
    base = discount['final_amount'] if discount else product.price
    is_popup = bool(discount) and discount.get('code') == POPUP_PROMO_CODE
    shipping = SHIPPING_COST if (is_popup and getattr(product, 'delivery_type', None) == 'physical') else 0
    return base + shipping, shipping


def _popup_pricing(product, session_shipping):
    """قیمت نهایی مسیر پاپ‌آپ — همیشه POPUP_FINAL_PRICE تومان (کتاب + ارسال).

    بدون توجه به قیمت پایه محصول، مبلغ قابل پرداخت از مسیر پاپ‌آپ ثابت است.
    """
    shipping = session_shipping if session_shipping > 0 else SHIPPING_COST
    final_amount = POPUP_FINAL_PRICE - shipping
    discount_amount = max(product.price - final_amount, 0)
    discount = {
        'code': POPUP_PROMO_CODE,
        'final_amount': final_amount,
        'discount_amount': discount_amount,
        'type': 'amount',
    }
    return discount, final_amount + shipping, shipping


def _login_redirect(product_id):
    """ری‌دایرکت به صفحه ورود با حفظ پروموی پاپ‌آپ در `next`.

    بدون این، بعد از ورود کاربر به `/shop/checkout/<id>` (بدون `?promo=KNOT50`) می‌رسد
    و به‌جای قیمت ۳۵۰,۰۰۰ پاپ‌آپ، قیمت ۴۰۰,۰۰۰ نمایش داده می‌شود.
    """
    target = f'/shop/checkout/{product_id}'
    if session.get('was_popup_path'):
        target += f'?promo={POPUP_PROMO_CODE}'
    return redirect(f'/shop/login?next={quote(target, safe="/")}')


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
    if not session.get('user_id'):
        promo = (request.args.get('promo') or '').strip()
        target = f'/shop/checkout/{product_id}'
        if promo == POPUP_PROMO_CODE:
            target += f'?promo={POPUP_PROMO_CODE}'
        return redirect(f'/shop/login?next={quote(target, safe="/")}')
    promo = (request.args.get('promo') or '').strip()
    shipping = SHIPPING_COST if (promo == POPUP_PROMO_CODE and product.delivery_type == 'physical') else 0
    final_price = POPUP_FINAL_PRICE if (promo == POPUP_PROMO_CODE and product.delivery_type == 'physical') else product.price
    session['checkout_shipping'] = shipping
    session['was_popup_path'] = (promo == POPUP_PROMO_CODE)
    return render_template('checkout.html', product=product, promo=promo,
                           shipping=shipping, final_price=final_price)


@shop_bp.route('/api/validate-discount', methods=['POST'])
def validate_discount():
    data = request.get_json() or {}
    try:
        product_id = int(data.get('product_id'))
    except (TypeError, ValueError):
        return jsonify({'valid': False, 'message': 'درخواست نامعتبر است'}), 400
    code = (data.get('code') or '').strip()
    product = Product.query.get_or_404(product_id)
    result = evaluate_discount(code, product)
    if not result:
        return jsonify({
            'valid': False,
            'message': 'کد تخفیف نامعتبر است یا برای این محصول قابل استفاده نیست.'
        })
    return jsonify({
        'valid': True,
        'code': result['code'],
        'discount_amount': result['discount_amount'],
        'final_amount': result['final_amount'],
        'original_amount': result['original_amount'],
        'message': f"کد تخفیف اعمال شد. مبلغ تخفیف: {result['discount_amount']:,} تومان"
    })


@shop_bp.route('/checkout/<int:product_id>/pay', methods=['POST'])
def pay(product_id):
    product = Product.query.get_or_404(product_id)
    if not session.get('user_id'):
        return _login_redirect(product_id)
    method = request.form.get('payment_method')

    if method not in ('online', 'card'):
        return render_template('checkout.html', product=product, error='روش پرداخت نامعتبر است',
                               promo='', shipping=0, final_price=product.price)

    discount_code = (request.form.get('discount_code') or '').strip()
    was_popup = session.get('was_popup_path', False)
    session_shipping = session.pop('checkout_shipping', 0)

    if was_popup and product.delivery_type == 'physical':
        # مسیر پاپ‌آپ: قیمت نهایی همیشه POPUP_FINAL_PRICE تومان است
        discount, amount, shipping = _popup_pricing(product, session_shipping)
        discount_code = discount['code']
    else:
        discount = evaluate_discount(discount_code, product)
        if discount:
            amount, shipping = compute_order_amount(product, discount)
        else:
            amount = product.price
            shipping = session_shipping

    if method == 'online':
        if discount:
            session['shop_discount'] = {
                'product_id': product_id,
                'code': discount['code'],
                'final_amount': discount['final_amount'],
                'discount_amount': discount['discount_amount'],
                'shipping': shipping,
            }
        else:
            session['was_popup_path'] = was_popup
            session.pop('shop_discount', None)
        return redirect(f'/shop/checkout/{product_id}/online')

    order = Order(
        user_id=session.get('user_id'),
        product_id=product_id,
        payment_method='card',
        amount=amount,
        discount_code=discount_code if discount else None,
        discount_amount=discount['discount_amount'] if discount else None,
        status='pending_payment'
    )
    db.session.add(order)
    db.session.commit()
    return redirect(f'/shop/card/{order.id}')


@shop_bp.route('/checkout/<int:product_id>/online', methods=['GET'])
def online_form(product_id):
    product = Product.query.get_or_404(product_id)
    disc = session.get('shop_discount')
    discount = disc if disc and disc.get('product_id') == product_id else None
    shipping = disc.get('shipping', 0) if disc else 0
    back_link = f'/shop/checkout/{product_id}'
    if discount and discount.get('code') == POPUP_PROMO_CODE:
        back_link += f'?promo={POPUP_PROMO_CODE}'
    return render_template('payment_online.html', product=product, discount=discount,
                           shipping=shipping, back_link=back_link)


def _resolve_discount(product, product_id, form_code):
    """کد تخفیف را از فرم یا سشن اعتبارسنجی می‌کند و نتیجه را برمی‌گرداند."""
    discount = evaluate_discount(form_code, product)
    if not discount:
        disc = session.get('shop_discount')
        if disc and disc.get('product_id') == product_id:
            discount = evaluate_discount(disc.get('code', ''), product)
    return discount


@shop_bp.route('/checkout/<int:product_id>/online', methods=['POST'])
def online_pay(product_id):
    product = Product.query.get_or_404(product_id)
    if not session.get('user_id'):
        return _login_redirect(product_id)

    full_name = (request.form.get('full_name') or '').strip()
    phone = (request.form.get('phone') or '').strip()
    address = (request.form.get('address') or '').strip()
    postal_code = (request.form.get('postal_code') or '').strip()

    if not full_name or not phone or not address or not postal_code:
        back_link = f'/shop/checkout/{product_id}'
        return render_template('payment_online.html', product=product, discount=None, shipping=0,
                               back_link=back_link,
                               error='لطفاً تمام فیلدها را پر کنید.')

    was_popup = session.get('was_popup_path', False)
    session_shipping = session.pop('checkout_shipping', 0)

    if was_popup and product.delivery_type == 'physical':
        # مسیر پاپ‌آپ: قیمت نهایی همیشه POPUP_FINAL_PRICE تومان است
        discount, amount, shipping = _popup_pricing(product, session_shipping)
        discount_code = discount['code']
    else:
        discount_code = (request.form.get('discount_code') or '').strip()
        # کد تأییدشده از سشن (مرحله قبل / همان که در این صفحه نمایش داده شده)
        # ارجح است؛ در صورت نبود، کد ورودی فرم واکشی می‌شود. در هر دو حالت
        # قیمت دوباره از سمت سرور محاسبه می‌شود و مبلغ درگاه همیشه با تخفیف است.
        discount = _resolve_discount(product, product_id, discount_code)
        if discount:
            amount, shipping = compute_order_amount(product, discount)
            discount_code = discount['code']
        else:
            amount = product.price
            shipping = session_shipping
    
    order = Order(
        user_id=session.get('user_id'),
        product_id=product_id,
        payment_method='online',
        amount=amount,
        discount_code=discount_code if discount else None,
        discount_amount=discount['discount_amount'] if discount else None,
        customer_name=full_name,
        customer_phone=phone,
        customer_address=address,
        customer_postal_code=postal_code,
        status='pending_payment'
    )
    db.session.add(order)
    db.session.commit()

    session.pop('shop_discount', None)

    print(f"[PAYMENT] online order={order.id} product={product.name} amount={amount} "
          f"shipping={shipping} code={discount_code if discount else None}")

    site_url = os.getenv('SITE_URL', request.host_url.rstrip('/'))
    callback_url = f'{site_url}/shop/verify/{order.id}'

    result = create_payment(
        amount_tomans=amount,
        description=f'خرید {product.name} - {full_name}',
        callback_url=callback_url
    )

    if result['success']:
        order.zarinpal_authority = result['authority']
        db.session.commit()
        return redirect(result['pay_url'])

    db.session.delete(order)
    db.session.commit()
    back_link = f'/shop/checkout/{product_id}'
    return render_template('payment_online.html', product=product, discount=None, shipping=0,
                           back_link=back_link,
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
        'pending_key':     'پرداخت تایید شد — در انتظار ارسال',
        'completed':       'تکمیل شد ✓',
        'cancelled':       'لغو شده',
    }
    return render_template('orders.html', orders=user_orders, status_label=status_label)
