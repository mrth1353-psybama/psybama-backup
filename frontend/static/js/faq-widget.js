(function () {
    let isLoading = false;

    function createWidget() {
        const btn = document.createElement('button');
        btn.className = 'faq-widget-btn';
        btn.setAttribute('aria-label', 'سوالات متداول');
        btn.textContent = '؟';

        const panel = document.createElement('div');
        panel.className = 'faq-widget-panel';
        panel.innerHTML = `
            <div class="faq-widget-header">
                <span>سوالات متداول</span>
                <button type="button" class="faq-widget-close" aria-label="بستن">✕</button>
            </div>
            <div class="faq-widget-messages"></div>
            <div class="faq-widget-input">
                <input type="text" placeholder="سوالت رو بپرس..." maxlength="300" />
                <button type="button" class="faq-widget-send">ارسال</button>
            </div>
        `;

        document.body.appendChild(btn);
        document.body.appendChild(panel);

        const messagesEl = panel.querySelector('.faq-widget-messages');
        const inputEl = panel.querySelector('input');
        const sendBtn = panel.querySelector('.faq-widget-send');
        const closeBtn = panel.querySelector('.faq-widget-close');

        appendMessage(messagesEl, 'assistant', 'سلام! درباره خدمات، قیمت‌ها یا رزرو مشاوره سوال داری؟');

        btn.addEventListener('click', () => {
            panel.classList.toggle('open');
            if (panel.classList.contains('open')) inputEl.focus();
        });
        closeBtn.addEventListener('click', () => panel.classList.remove('open'));

        function send() {
            const text = inputEl.value.trim();
            if (!text || isLoading) return;

            appendMessage(messagesEl, 'user', text);
            inputEl.value = '';
            isLoading = true;
            sendBtn.disabled = true;

            fetch('/api/faq/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            })
                .then((res) => res.json())
                .then((data) => {
                    appendMessage(messagesEl, 'assistant', data.reply || data.message || 'خطایی رخ داد.');
                })
                .catch(() => {
                    appendMessage(messagesEl, 'assistant', 'ارتباط برقرار نشد. دوباره تلاش کن.');
                })
                .finally(() => {
                    isLoading = false;
                    sendBtn.disabled = false;
                });
        }

        sendBtn.addEventListener('click', send);
        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') send();
        });
    }

    function appendMessage(container, role, text) {
        const el = document.createElement('div');
        el.className = `faq-widget-msg ${role}`;
        el.textContent = text;
        container.appendChild(el);
        container.scrollTop = container.scrollHeight;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
    } else {
        createWidget();
    }
})();
