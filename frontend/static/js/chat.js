'use strict';

const Chat = (() => {
    let conversationId = null;
    let isLoading = false;

    const messagesEl  = document.getElementById('chatMessages');
    const inputEl     = document.getElementById('chatInput');
    const btnSend     = document.getElementById('btnSend');
    const btnNewChat  = document.getElementById('btnNewChat');
    const btnLogout   = document.getElementById('btnLogout');
    const convListEl  = document.getElementById('convList');

    const WELCOME_TEXT = 'سلام. به سای‌باما خوش آمدی.\nاینجا یک حریم امن و بدون قضاوت است؛ هر زمان که آماده بودی، بنویس که در محیط کارت چه می‌گذرد.';

    function formatTime(isoString) {
        if (!isoString) return '';
        const d = new Date(isoString);
        return d.toLocaleTimeString('fa-IR', {hour: '2-digit', minute: '2-digit'});
    }

    function formatDate(isoString) {
        if (!isoString) return '';
        const d = new Date(isoString);
        return d.toLocaleDateString('fa-IR', {month: 'short', day: 'numeric'});
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.appendChild(document.createTextNode(text));
        return d.innerHTML;
    }

    function renderMarkdown(text) {
        return escapeHtml(text)
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    function scrollToBottom(smooth = true) {
        messagesEl.scrollTo({
            top: messagesEl.scrollHeight,
            behavior: smooth ? 'smooth' : 'instant'
        });
    }

    function appendMessage(role, content, timestamp) {
        const welcomeMsg = document.getElementById('welcomeMsg');
        if (welcomeMsg) welcomeMsg.style.display = 'none';

        const isUser = role === 'user';
        const row = document.createElement('div');
        row.className = `message-row ${role}`;
        row.innerHTML = `
            <div class="message-avatar">${isUser ? '👤' : 'س'}</div>
            <div>
                <div class="message-bubble">${isUser ? escapeHtml(content) : renderMarkdown(content)}</div>
                <div class="message-time">${timestamp ? formatTime(timestamp) : nowTime()}</div>
            </div>`;
        messagesEl.appendChild(row);
        scrollToBottom();
    }

    function nowTime() {
        return new Date().toLocaleTimeString('fa-IR', {hour: '2-digit', minute: '2-digit'});
    }

    function showTyping() {
        const row = document.createElement('div');
        row.className = 'typing-row';
        row.id = 'typingIndicator';
        row.innerHTML = `
            <div class="message-avatar" style="background:linear-gradient(135deg,var(--ocean-blue),var(--sage-teal));color:white;width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:var(--font-title);font-size:0.9rem;">س</div>
            <div class="typing-bubble">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>`;
        messagesEl.appendChild(row);
        scrollToBottom();
    }

    function hideTyping() {
        const el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }

    function setInputEnabled(enabled) {
        inputEl.disabled = !enabled;
        btnSend.disabled = !enabled;
        if (enabled) inputEl.focus();
    }

    // ── Sidebar ──────────────────────────────────────

    async function loadConversations() {
        try {
            const res = await fetch('/api/chat/conversations');
            if (!res.ok) return;
            const data = await res.json();
            renderConvList(data.conversations);
        } catch (e) {
            console.error('Failed to load conversations', e);
        }
    }

    function renderConvList(convs) {
        if (!convListEl) return;
        convListEl.innerHTML = '';

        if (!convs || convs.length === 0) {
            convListEl.innerHTML = '<div class="sidebar-empty">گفتگویی وجود ندارد</div>';
            return;
        }

        convs.forEach(c => {
            const item = document.createElement('div');
            item.className = 'conv-item' + (c.id === conversationId ? ' active' : '');
            item.dataset.id = c.id;
            item.innerHTML = `
                <div class="conv-item-body">
                    <span class="conv-preview">${escapeHtml(c.preview)}</span>
                    <span class="conv-date">${formatDate(c.started_at)}</span>
                </div>
                <button class="conv-delete-btn" title="حذف گفتگو" data-id="${c.id}">🗑</button>`;

            item.querySelector('.conv-item-body').addEventListener('click', () => openConversation(c.id));

            item.querySelector('.conv-delete-btn').addEventListener('click', async (e) => {
                e.stopPropagation();
                if (!confirm('این گفتگو حذف شود؟')) return;
                await deleteConversation(c.id);
            });

            convListEl.appendChild(item);
        });
    }

    async function deleteConversation(convId) {
        try {
            const res = await fetch(`/api/chat/conversations/${convId}`, {method: 'DELETE'});
            if (!res.ok) return;
            if (convId === conversationId) {
                conversationId = null;
                messagesEl.innerHTML = '';
                showWelcome();
            }
            loadConversations();
        } catch (e) {
            console.error('Failed to delete conversation', e);
        }
    }

    async function openConversation(convId) {
        if (convId === conversationId && !isLoading) return;
        conversationId = convId;

        // clear messages
        messagesEl.innerHTML = '';

        try {
            const res = await fetch(`/api/chat/history/${convId}`);
            const data = await res.json();
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(m => appendMessage(m.role, m.content, m.timestamp));
            } else {
                showWelcome();
            }
        } catch (e) {
            console.error('Failed to load conversation', e);
        }

        // update active state
        document.querySelectorAll('.conv-item').forEach(el => {
            el.classList.toggle('active', parseInt(el.dataset.id) === convId);
        });
    }

    function showWelcome() {
        const welcome = document.createElement('div');
        welcome.className = 'welcome-msg';
        welcome.id = 'welcomeMsg';
        welcome.innerHTML = '<p>سلام. به سای‌باما خوش آمدی.<br>اینجا یک حریم امن و بدون قضاوت است؛ هر زمان که آماده بودی، بنویس که در محیط کارت چه می‌گذرد.</p>';
        messagesEl.appendChild(welcome);
    }

    // ── Send message ──────────────────────────────────

    async function sendMessage() {
        const text = inputEl.value.trim();
        if (!text || isLoading) return;

        isLoading = true;
        setInputEnabled(false);

        appendMessage('user', text);
        inputEl.value = '';
        autoResize();
        showTyping();

        try {
            const res = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text, conversation_id: conversationId})
            });
            const data = await res.json();

            hideTyping();

            if (!res.ok) {
                if (res.status === 401) { location.reload(); return; }
                appendMessage('assistant', 'متأسفم، مشکلی پیش آمد. لطفاً دوباره امتحان کنید.');
                return;
            }

            conversationId = data.conversation_id;
            appendMessage('assistant', data.reply);
            loadConversations();

        } catch (e) {
            hideTyping();
            appendMessage('assistant', 'خطا در اتصال به سرور. لطفاً اتصال اینترنت خود را بررسی کنید.');
        } finally {
            isLoading = false;
            setInputEnabled(true);
        }
    }

    function autoResize() {
        inputEl.style.height = 'auto';
        inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
    }

    async function startNewConversation() {
        try {
            const res = await fetch('/api/chat/new-conversation', {method: 'POST'});
            const data = await res.json();
            conversationId = data.conversation_id;

            messagesEl.innerHTML = '';
            showWelcome();
            loadConversations();
        } catch (e) {
            console.error('Failed to create new conversation', e);
        }
    }

    async function logout() {
        await fetch('/api/auth/logout', {method: 'POST'});
        location.reload();
    }

    function onAuthSuccess() {
        setInputEnabled(true);
        appendMessage('assistant', WELCOME_TEXT);
        loadConversations();
    }

    function init() {
        btnSend.addEventListener('click', sendMessage);
        btnNewChat.addEventListener('click', startNewConversation);
        btnLogout.addEventListener('click', logout);

        inputEl.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        inputEl.addEventListener('input', autoResize);
    }

    document.addEventListener('DOMContentLoaded', init);

    return {onAuthSuccess};
})();
