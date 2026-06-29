'use strict';

const Admin = (() => {
    const loginModal = document.getElementById('adminLoginModal');
    const adminPanel = document.getElementById('adminPanel');
    const passwordInput = document.getElementById('adminPasswordInput');
    const loginError = document.getElementById('adminLoginError');
    const btnLogin = document.getElementById('btnAdminLogin');
    const btnLogout = document.getElementById('btnAdminLogout');

    let currentUsersPage = 1;
    let currentConvsPage = 1;

    // ── Auth ──────────────────────────────────────────

    async function checkAdminStatus() {
        try {
            const res = await fetch('/admin/status');
            const data = await res.json();
            if (data.logged_in) {
                showPanel();
            }
        } catch (e) {}
    }

    async function adminLogin() {
        const pw = passwordInput.value.trim();
        if (!pw) return;

        loginError.classList.add('hidden');
        btnLogin.disabled = true;
        btnLogin.textContent = '...';

        try {
            const res = await fetch('/admin/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: pw})
            });
            const data = await res.json();

            if (res.ok) {
                showPanel();
            } else {
                loginError.textContent = data.message || 'پسورد اشتباه است';
                loginError.classList.remove('hidden');
                passwordInput.value = '';
                passwordInput.focus();
            }
        } catch (e) {
            loginError.textContent = 'خطا در اتصال';
            loginError.classList.remove('hidden');
        } finally {
            btnLogin.disabled = false;
            btnLogin.textContent = 'ورود';
        }
    }

    async function adminLogout() {
        await fetch('/admin/logout', {method: 'POST'});
        location.reload();
    }

    function showPanel() {
        loginModal.classList.add('hidden');
        adminPanel.classList.remove('hidden');
        loadStats();
        loadUsers();
        loadConversations();
        loadContacts();
        loadOrders();
        loadProducts();
    }

    // ── Stats ─────────────────────────────────────────

    async function loadStats() {
        try {
            const res = await fetch('/admin/stats');
            const data = await res.json();
            document.getElementById('statUsers').textContent = data.total_users;
            document.getElementById('statVerified').textContent = data.verified_users;
            document.getElementById('statConvs').textContent = data.total_conversations;
            document.getElementById('statMsgs').textContent = data.total_messages;
            document.getElementById('statAssess').textContent = data.total_assessments;

            const badge = document.getElementById('unreadBadge');
            if (data.unread_contact_requests > 0) {
                badge.textContent = data.unread_contact_requests;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }

            const ordersBadge = document.getElementById('pendingOrdersBadge');
            if (data.pending_orders > 0) {
                ordersBadge.textContent = data.pending_orders;
                ordersBadge.classList.remove('hidden');
            } else {
                ordersBadge.classList.add('hidden');
            }
        } catch (e) {}
    }

    // ── Users ─────────────────────────────────────────

    async function loadUsers(page = 1) {
        currentUsersPage = page;
        const tbody = document.getElementById('usersTableBody');

        try {
            const res = await fetch(`/admin/users?page=${page}`);
            const data = await res.json();

            if (!data.users.length) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:2rem">هنوز کاربری ثبت‌نام نکرده است</td></tr>';
                return;
            }

            tbody.innerHTML = data.users.map(u => `
                <tr>
                    <td>${u.id}</td>
                    <td style="direction:ltr;text-align:left">${u.phone_number}</td>
                    <td><span class="badge ${u.verified ? 'badge-success' : 'badge-warning'}">${u.verified ? 'تأیید شده' : 'در انتظار'}</span></td>
                    <td>${formatDateTime(u.created_at)}</td>
                    <td>${u.conversation_count}</td>
                </tr>`).join('');

            renderPagination('usersPagination', data.pages, page, loadUsers);

        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center" style="color:var(--error);padding:2rem">خطا در بارگذاری</td></tr>';
        }
    }

    // ── Conversations ─────────────────────────────────

    async function loadConversations(page = 1) {
        currentConvsPage = page;
        const tbody = document.getElementById('convsTableBody');

        try {
            const res = await fetch(`/admin/conversations?page=${page}`);
            const data = await res.json();

            if (!data.conversations.length) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:2rem">هنوز گفتگویی انجام نشده است</td></tr>';
                return;
            }

            tbody.innerHTML = data.conversations.map(c => `
                <tr>
                    <td>${c.id}</td>
                    <td style="direction:ltr;text-align:left">${c.phone_number || '—'}</td>
                    <td>${c.message_count}</td>
                    <td>${formatDateTime(c.started_at)}</td>
                    <td><button class="btn btn-outline btn-sm" onclick="Admin.viewConversation(${c.id})">مشاهده</button></td>
                </tr>`).join('');

        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center" style="color:var(--error);padding:2rem">خطا در بارگذاری</td></tr>';
        }
    }

    async function viewConversation(convId) {
        const viewer = document.getElementById('convViewer');
        const msgList = document.getElementById('convMessagesList');
        const title = document.getElementById('convViewerTitle');

        viewer.classList.remove('hidden');
        msgList.innerHTML = '<div class="text-center text-muted" style="padding:1rem">در حال بارگذاری...</div>';
        title.textContent = `گفتگوی #${convId}`;

        viewer.scrollIntoView({behavior: 'smooth', block: 'start'});

        try {
            const res = await fetch(`/admin/messages/${convId}`);
            const data = await res.json();

            if (!data.messages.length) {
                msgList.innerHTML = '<div class="text-center text-muted" style="padding:1rem">این گفتگو پیامی ندارد</div>';
                return;
            }

            title.textContent = `گفتگوی #${convId} — ${data.user_phone}`;

            msgList.innerHTML = data.messages.map(m => `
                <div class="conv-message ${m.role}">
                    <div class="conv-message-role">${m.role === 'user' ? '👤 کاربر' : '🤖 سای‌باما'}</div>
                    <div class="conv-message-text">${escapeHtml(m.content)}</div>
                </div>`).join('');

        } catch (e) {
            msgList.innerHTML = '<div class="text-center" style="color:var(--error);padding:1rem">خطا در بارگذاری</div>';
        }
    }

    // ── Orders ────────────────────────────────────────

    let currentOrderId = null;

    const STATUS_LABEL = {
        pending_payment: '⏳ در انتظار تأیید پرداخت',
        pending_key:     '🔑 منتظر کلید',
        completed:       '✅ تکمیل شده',
        cancelled:       '❌ لغو شده',
    };
    const METHOD_LABEL = { online: 'آنلاین', card: 'کارت به کارت' };

    async function loadOrders() {
        const tbody = document.getElementById('ordersTableBody');
        try {
            const res  = await fetch('/admin/orders');
            const data = await res.json();

            if (!data.orders.length) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted" style="padding:2rem">هنوز سفارشی ثبت نشده</td></tr>';
                return;
            }

            tbody.innerHTML = data.orders.map(o => {
                const needsKey = o.status === 'pending_key';
                const isPending = o.status === 'pending_payment';
                return `
                <tr style="${(needsKey || isPending) ? 'background:#FFF8E1;font-weight:bold' : ''}">
                    <td>${o.id}</td>
                    <td style="direction:ltr;text-align:left">${o.phone_number}</td>
                    <td>${escapeHtml(o.product_name)}</td>
                    <td style="direction:ltr;text-align:left">${Number(o.amount).toLocaleString()}</td>
                    <td>${METHOD_LABEL[o.payment_method] || o.payment_method}</td>
                    <td>${STATUS_LABEL[o.status] || o.status}</td>
                    <td style="white-space:nowrap">${formatDateTime(o.created_at)}</td>
                    <td style="white-space:nowrap;display:flex;gap:0.4rem">
                        ${needsKey ? `<button class="btn btn-outline btn-sm" onclick="Admin.openKeyPanel(${o.id}, '${escapeHtml(o.product_name)}')">ثبت کلید</button>` : ''}
                        ${isPending ? `<button class="btn btn-outline btn-sm" style="color:var(--sage-teal)" onclick="Admin.openKeyPanel(${o.id}, '${escapeHtml(o.product_name)}')">تأیید + کلید</button>` : ''}
                        ${o.status !== 'cancelled' && o.status !== 'completed' ? `<button class="btn btn-sm" style="background:#FEE2E2;color:#B91C1C;border:none" onclick="Admin.cancelOrder(${o.id})">لغو</button>` : ''}
                        ${o.spotplayer_key ? `<span style="font-size:0.75rem;color:var(--text-muted)">🔑 ${escapeHtml(o.spotplayer_key)}</span>` : ''}
                    </td>
                </tr>`;
            }).join('');

        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="color:var(--error);padding:2rem">خطا در بارگذاری</td></tr>';
        }
    }

    function openKeyPanel(orderId, productName) {
        currentOrderId = orderId;
        document.getElementById('keyPanelProduct').textContent = `سفارش #${orderId} — ${productName}`;
        document.getElementById('keyInput').value = '';
        document.getElementById('keyPanel').classList.remove('hidden');
        document.getElementById('keyPanel').scrollIntoView({behavior: 'smooth'});
    }

    function closeKeyPanel() {
        document.getElementById('keyPanel').classList.add('hidden');
        currentOrderId = null;
    }

    async function submitKey() {
        const key = document.getElementById('keyInput').value.trim();
        if (!key) { alert('کلید را وارد کنید'); return; }
        try {
            const res  = await fetch(`/admin/orders/${currentOrderId}/set-key`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key})
            });
            const data = await res.json();
            if (data.success) {
                closeKeyPanel();
                await loadOrders();
                await loadStats();
                alert('کلید ثبت شد و SMS ارسال شد.');
            }
        } catch (e) { alert('خطا در ثبت کلید'); }
    }

    async function cancelOrder(id) {
        if (!confirm('این سفارش لغو شود؟')) return;
        try {
            await fetch(`/admin/orders/${id}/cancel`, {method: 'POST'});
            await loadOrders();
            await loadStats();
        } catch (e) {}
    }

    // ── Products ──────────────────────────────────────

    async function loadProducts() {
        const grid = document.getElementById('productsGrid');
        try {
            const res  = await fetch('/admin/products');
            const data = await res.json();
            grid.innerHTML = data.products.map(p => `
                <div style="background:var(--pure-white);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.25rem">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
                        <span style="font-size:0.75rem;color:var(--text-muted)">#${p.id}</span>
                        <span class="badge ${p.is_active ? 'badge-success' : 'badge-warning'}">${p.is_active ? 'فعال' : 'غیرفعال'}</span>
                    </div>
                    <div class="form-group" style="margin-bottom:0.5rem">
                        <label class="form-label" style="font-size:0.78rem">نام</label>
                        <input id="pname-${p.id}" class="form-input" style="font-size:0.85rem" value="${escapeHtml(p.name)}">
                    </div>
                    <div class="form-group" style="margin-bottom:0.5rem">
                        <label class="form-label" style="font-size:0.78rem">توضیحات</label>
                        <textarea id="pdesc-${p.id}" class="form-input" rows="2" style="font-size:0.82rem;resize:vertical">${escapeHtml(p.description || '')}</textarea>
                    </div>
                    <div class="form-group" style="margin-bottom:0.75rem">
                        <label class="form-label" style="font-size:0.78rem">قیمت (تومان)</label>
                        <input id="pprice-${p.id}" class="form-input" style="font-size:0.85rem;direction:ltr" type="number" value="${p.price}">
                    </div>
                    <div style="display:flex;gap:0.5rem">
                        <button class="btn btn-primary btn-sm" style="flex:1" onclick="Admin.saveProduct(${p.id})">ذخیره</button>
                        <button class="btn btn-sm" style="background:#FEE2E2;color:#B91C1C;border:none" onclick="Admin.toggleProduct(${p.id}, ${!p.is_active})">${p.is_active ? 'غیرفعال' : 'فعال‌سازی'}</button>
                    </div>
                </div>`).join('');
        } catch (e) {
            grid.innerHTML = '<p style="color:var(--error)">خطا در بارگذاری محصولات</p>';
        }
    }

    async function saveProduct(id) {
        const name  = document.getElementById(`pname-${id}`).value.trim();
        const desc  = document.getElementById(`pdesc-${id}`).value.trim();
        const price = parseInt(document.getElementById(`pprice-${id}`).value);
        if (!name || !price) { alert('نام و قیمت الزامی است'); return; }
        try {
            await fetch(`/admin/products/${id}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, description: desc, price})
            });
            await loadProducts();
        } catch (e) { alert('خطا در ذخیره'); }
    }

    async function toggleProduct(id, isActive) {
        try {
            await fetch(`/admin/products/${id}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({is_active: isActive})
            });
            await loadProducts();
        } catch (e) {}
    }

    // ── Contacts ──────────────────────────────────────

    async function loadContacts() {
        const tbody = document.getElementById('contactsTableBody');
        try {
            const res = await fetch('/admin/contact-requests');
            const data = await res.json();

            if (!data.requests.length) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding:2rem">هنوز درخواستی ثبت نشده است</td></tr>';
                return;
            }

            tbody.innerHTML = data.requests.map(r => `
                <tr id="contact-row-${r.id}" style="${r.is_read ? '' : 'background:#FFF8E1;font-weight:bold'}">
                    <td>${r.id}</td>
                    <td>${escapeHtml(r.name)}</td>
                    <td style="direction:ltr;text-align:left">${escapeHtml(r.phone)}</td>
                    <td style="max-width:300px;word-break:break-word">${escapeHtml(r.message || '—')}</td>
                    <td style="white-space:nowrap">${formatDateTime(r.created_at)}</td>
                    <td>
                        ${r.is_read
                            ? '<span class="badge badge-success">خوانده شد</span>'
                            : `<button class="btn btn-outline btn-sm" onclick="Admin.markContactRead(${r.id})">علامت‌گذاری</button>`}
                    </td>
                    <td>
                        <button class="btn btn-sm" style="background:#FEE2E2;color:#B91C1C;border:none" onclick="Admin.deleteContact(${r.id})">🗑 حذف</button>
                    </td>
                </tr>`).join('');

        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="color:var(--error);padding:2rem">خطا در بارگذاری</td></tr>';
        }
    }

    async function markContactRead(id) {
        try {
            await fetch(`/admin/contact-requests/${id}/read`, {method: 'POST'});
            await loadContacts();
            await loadStats();
        } catch (e) {}
    }

    async function deleteContact(id) {
        if (!confirm('این درخواست حذف شود؟')) return;
        try {
            await fetch(`/admin/contact-requests/${id}/delete`, {method: 'POST'});
            await loadContacts();
            await loadStats();
        } catch (e) {}
    }

    // ── Search ────────────────────────────────────────

    async function doSearch() {
        const q = document.getElementById('searchInput').value.trim();
        const resultsEl = document.getElementById('searchResults');

        if (q.length < 2) {
            resultsEl.innerHTML = '<div class="alert alert-info">حداقل ۲ کاراکتر وارد کنید</div>';
            return;
        }

        resultsEl.innerHTML = '<div class="text-center text-muted" style="padding:1rem">در حال جستجو...</div>';

        try {
            const res = await fetch(`/admin/search?q=${encodeURIComponent(q)}`);
            const data = await res.json();

            if (!data.results.length) {
                resultsEl.innerHTML = '<div class="alert alert-info">نتیجه‌ای یافت نشد</div>';
                return;
            }

            const highlighted = text => text.replace(
                new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'),
                m => `<mark style="background:#FEF08A;padding:0 2px;border-radius:2px">${m}</mark>`
            );

            resultsEl.innerHTML = `
                <p class="text-muted" style="margin-bottom:1rem">
                    ${data.count} نتیجه برای «${escapeHtml(q)}»
                </p>
                <div class="table-wrapper">
                    <table class="data-table">
                        <thead><tr><th>نقش</th><th>محتوا</th><th>زمان</th><th>گفتگو</th></tr></thead>
                        <tbody>
                            ${data.results.map(m => `
                                <tr>
                                    <td><span class="badge ${m.role === 'user' ? 'badge-info' : 'badge-success'}">${m.role === 'user' ? 'کاربر' : 'سای‌باما'}</span></td>
                                    <td style="max-width:400px;word-break:break-word">${highlighted(escapeHtml(m.content))}</td>
                                    <td style="white-space:nowrap">${formatDateTime(m.timestamp)}</td>
                                    <td><button class="btn btn-ghost btn-sm" onclick="Admin.viewConversation(${m.conversation_id})">#${m.conversation_id}</button></td>
                                </tr>`).join('')}
                        </tbody>
                    </table>
                </div>`;

        } catch (e) {
            resultsEl.innerHTML = '<div class="alert alert-error">خطا در جستجو</div>';
        }
    }

    // ── Helpers ───────────────────────────────────────

    function formatDateTime(iso) {
        if (!iso) return '—';
        const d = new Date(iso);
        const date = d.toLocaleDateString('fa-IR');
        const time = d.toLocaleTimeString('fa-IR', {hour: '2-digit', minute: '2-digit'});
        return date + ' — ' + time;
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.appendChild(document.createTextNode(String(text)));
        return d.innerHTML;
    }

    function renderPagination(containerId, totalPages, current, callback) {
        const el = document.getElementById(containerId);
        if (totalPages <= 1) { el.innerHTML = ''; return; }

        let html = '';
        for (let i = 1; i <= totalPages; i++) {
            html += `<button class="btn ${i === current ? 'btn-primary' : 'btn-outline'} btn-sm"
                             onclick="${callback.name}(${i})">${i}</button>`;
        }
        el.innerHTML = html;
    }

    // ── Tabs ──────────────────────────────────────────

    function initTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
            });
        });
    }

    // ── Init ──────────────────────────────────────────

    function init() {
        btnLogin.addEventListener('click', adminLogin);
        btnLogout.addEventListener('click', adminLogout);
        passwordInput.addEventListener('keydown', e => { if (e.key === 'Enter') adminLogin(); });

        document.getElementById('btnSearch').addEventListener('click', doSearch);
        document.getElementById('searchInput').addEventListener('keydown', e => {
            if (e.key === 'Enter') doSearch();
        });

        document.getElementById('btnCloseViewer').addEventListener('click', () => {
            document.getElementById('convViewer').classList.add('hidden');
        });

        initTabs();
        checkAdminStatus();
    }

    document.addEventListener('DOMContentLoaded', init);

    return {viewConversation, markContactRead, deleteContact,
            openKeyPanel, closeKeyPanel, submitKey, cancelOrder,
            saveProduct, toggleProduct};
})();
