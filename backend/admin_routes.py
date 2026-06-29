import io
import os
from flask import Blueprint, request, jsonify, session, send_file, render_template
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from auth import admin_required
from models import db, User, Conversation, Message, Assessment, ContactRequest, Order, Product
from models import iran_now

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_bp.route('')
def admin_index():
    return render_template('admin.html')


@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if not data or not data.get('password'):
        return jsonify({'error': 'password_required'}), 400

    if data['password'] == os.getenv('ADMIN_PASSWORD', 'admin1234'):
        session['admin_logged_in'] = True
        return jsonify({'success': True})

    return jsonify({'error': 'invalid_password', 'message': 'پسورد اشتباه است'}), 401


@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return jsonify({'success': True})


@admin_bp.route('/status')
def admin_status():
    return jsonify({'logged_in': bool(session.get('admin_logged_in'))})


@admin_bp.route('/users')
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    users_page = (User.query
                  .order_by(User.created_at.desc())
                  .paginate(page=page, per_page=per_page, error_out=False))

    return jsonify({
        'users': [u.to_dict() for u in users_page.items],
        'total': users_page.total,
        'pages': users_page.pages,
        'current_page': page
    })


@admin_bp.route('/conversations')
@admin_required
def list_conversations():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    convs_page = (Conversation.query
                  .order_by(Conversation.started_at.desc())
                  .paginate(page=page, per_page=per_page, error_out=False))

    result = []
    for c in convs_page.items:
        d = c.to_dict()
        if c.user:
            d['phone_number'] = c.user.phone_number
        result.append(d)

    return jsonify({
        'conversations': result,
        'total': convs_page.total,
        'pages': convs_page.pages,
        'current_page': page
    })


@admin_bp.route('/messages/<int:conv_id>')
@admin_required
def get_messages(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    user_phone = conv.user.phone_number if conv.user else 'ناشناس'

    return jsonify({
        'conversation_id': conv_id,
        'user_phone': user_phone,
        'started_at': conv.started_at.isoformat() if conv.started_at else None,
        'messages': [m.to_dict() for m in conv.messages]
    })


@admin_bp.route('/search')
@admin_required
def search_messages():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': [], 'message': 'حداقل ۲ کاراکتر وارد کنید'})

    results = (Message.query
               .filter(Message.content.contains(q))
               .order_by(Message.timestamp.desc())
               .limit(100)
               .all())

    output = []
    for m in results:
        d = m.to_dict()
        if m.conversation and m.conversation.user:
            d['phone_number'] = m.conversation.user.phone_number
        output.append(d)

    return jsonify({'results': output, 'count': len(output)})


@admin_bp.route('/contact-requests')
@admin_required
def list_contact_requests():
    requests_list = (ContactRequest.query
                     .order_by(ContactRequest.created_at.desc())
                     .all())
    return jsonify({'requests': [r.to_dict() for r in requests_list]})


@admin_bp.route('/contact-requests/<int:req_id>/read', methods=['POST'])
@admin_required
def mark_contact_read(req_id):
    cr = ContactRequest.query.get_or_404(req_id)
    cr.is_read = True
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/contact-requests/<int:req_id>/delete', methods=['POST'])
@admin_required
def delete_contact_request(req_id):
    cr = ContactRequest.query.get_or_404(req_id)
    db.session.delete(cr)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/orders')
@admin_required
def list_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify({'orders': [o.to_dict() for o in orders]})


@admin_bp.route('/orders/<int:order_id>/set-key', methods=['POST'])
@admin_required
def set_order_key(order_id):
    data = request.get_json()
    key = (data or {}).get('key', '').strip()
    if not key:
        return jsonify({'error': 'key_required'}), 400

    order = Order.query.get_or_404(order_id)
    order.spotplayer_key = key
    order.status = 'completed'
    order.completed_at = iran_now()
    db.session.commit()

    # Send key via SMS
    try:
        from sms_service import send_sms
        phone = order.user.phone_number
        product_name = order.product.name
        msg = f'سای‌باما: کلید دسترسی به {product_name} شما:\n{key}\nبا موفقیت فعال شد.'
        send_sms(phone, msg)
    except Exception:
        pass

    return jsonify({'success': True})


@admin_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@admin_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'cancelled'
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/products')
@admin_required
def list_products():
    products = Product.query.all()
    return jsonify({'products': [p.to_dict() for p in products]})


@admin_bp.route('/products/<int:product_id>', methods=['POST'])
@admin_required
def update_product(product_id):
    data = request.get_json()
    product = Product.query.get_or_404(product_id)
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = int(data['price'])
    if 'is_active' in data:
        product.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'success': True, 'product': product.to_dict()})


@admin_bp.route('/stats')
@admin_required
def get_stats():
    pending = Order.query.filter(Order.status.in_(['pending_payment', 'pending_key'])).count()
    return jsonify({
        'total_users': User.query.count(),
        'verified_users': User.query.filter_by(is_verified=True).count(),
        'total_conversations': Conversation.query.count(),
        'total_messages': Message.query.count(),
        'total_assessments': Assessment.query.count(),
        'total_contact_requests': ContactRequest.query.count(),
        'unread_contact_requests': ContactRequest.query.filter_by(is_read=False).count(),
        'pending_orders': pending,
    })


@admin_bp.route('/export')
@admin_required
def export_excel():
    wb = Workbook()

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='1D5FA6')
    center_align = Alignment(horizontal='center', vertical='center')

    # Sheet 1: Users
    ws_users = wb.active
    ws_users.title = 'کاربران'
    headers_u = ['شناسه', 'شماره موبایل', 'تأیید شده', 'تاریخ ثبت‌نام', 'تعداد گفتگو']
    ws_users.append(headers_u)
    for cell in ws_users[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for u in User.query.order_by(User.created_at).all():
        ws_users.append([
            u.id,
            u.phone_number,
            'بله' if u.is_verified else 'خیر',
            str(u.created_at)[:19] if u.created_at else '',
            len(u.conversations)
        ])

    ws_users.column_dimensions['B'].width = 20
    ws_users.column_dimensions['D'].width = 22

    # Sheet 2: Messages
    ws_msgs = wb.create_sheet('گفتگوها')
    headers_m = ['شناسه گفتگو', 'شماره موبایل', 'نقش', 'محتوا', 'زمان']
    ws_msgs.append(headers_m)
    for cell in ws_msgs[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    messages = (Message.query
                .join(Conversation)
                .join(User)
                .order_by(Conversation.id, Message.timestamp)
                .all())

    for m in messages:
        phone = m.conversation.user.phone_number if (m.conversation and m.conversation.user) else ''
        role_fa = 'کاربر' if m.role == 'user' else 'سای‌باما'
        ws_msgs.append([
            m.conversation_id,
            phone,
            role_fa,
            m.content,
            str(m.timestamp)[:19] if m.timestamp else ''
        ])

    ws_msgs.column_dimensions['B'].width = 18
    ws_msgs.column_dimensions['D'].width = 60
    ws_msgs.column_dimensions['E'].width = 22

    # Sheet 3: Assessments
    ws_assess = wb.create_sheet('پرسشنامه‌ها')
    headers_a = ['شناسه', 'شماره موبایل', 'خستگی عاطفی', 'سطح EE', 'مسخ شخصیت', 'سطح DP', 'کفایت فردی', 'سطح PA', 'تاریخ']
    ws_assess.append(headers_a)
    for cell in ws_assess[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for a in Assessment.query.all():
        phone = a.user.phone_number if a.user else ''
        level_map = {'low': 'پایین', 'moderate': 'متوسط', 'high': 'بالا'}
        ws_assess.append([
            a.id, phone,
            a.emotional_exhaustion, level_map.get(a.ee_level, ''),
            a.depersonalization, level_map.get(a.dp_level, ''),
            a.personal_accomplishment, level_map.get(a.pa_level, ''),
            str(a.completed_at)[:19] if a.completed_at else ''
        ])

    # Sheet 4: Contact Requests
    ws_contacts = wb.create_sheet('درخواست مشاوره')
    headers_c = ['شناسه', 'نام', 'شماره موبایل', 'پیام', 'تاریخ', 'خوانده شده']
    ws_contacts.append(headers_c)
    for cell in ws_contacts[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for cr in ContactRequest.query.order_by(ContactRequest.created_at.desc()).all():
        ws_contacts.append([
            cr.id,
            cr.name,
            cr.phone,
            cr.message or '',
            str(cr.created_at)[:19] if cr.created_at else '',
            'بله' if cr.is_read else 'خیر'
        ])

    ws_contacts.column_dimensions['B'].width = 20
    ws_contacts.column_dimensions['C'].width = 18
    ws_contacts.column_dimensions['D'].width = 40
    ws_contacts.column_dimensions['E'].width = 22

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='psybama_export.xlsx'
    )
