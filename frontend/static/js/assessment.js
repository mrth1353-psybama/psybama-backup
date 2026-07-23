'use strict';

const MBI_QUESTIONS = [
    'در کارم احساس خستگی عاطفی می‌کنم.',
    'در پایان روز کاری احساس می‌کنم توانم تحلیل رفته است.',
    'صبح که بیدار می‌شوم و باید به محل کار بروم، خسته به نظر می‌رسم.',
    'به‌خوبی می‌توانم احساس کسانی را که با آنها کار می‌کنم درک کنم.',
    'احساس می‌کنم با برخی مراجعین/همکارانم مثل یک شیء رفتار می‌کنم.',
    'تمام روز با آدم‌ها کار کردن برایم سخت است.',
    'با مشکلات مراجعین/همکارانم به‌طور مؤثر برخورد می‌کنم.',
    'در کارم احساس فرسودگی می‌کنم.',
    'احساس می‌کنم از طریق کارم تأثیر مثبتی بر زندگی دیگران می‌گذارم.',
    'از زمانی که در این کار هستم، نسبت به مردم بی‌تفاوت‌تر شده‌ام.',
    'نگرانم که این کار مرا احساساتی‌تر می‌کند.',
    'انرژی و سرزندگی زیادی دارم.',
    'در کارم احساس سرخوردگی می‌کنم.',
    'احساس می‌کنم خیلی سخت کار می‌کنم.',
    'واقعاً برایم اهمیت ندارد که با برخی مراجعین چه اتفاقی می‌افتد.',
    'کار مستقیم با مردم خیلی برایم استرس‌زاست.',
    'می‌توانم فضای آرامی در محیط کار ایجاد کنم.',
    'بعد از کار کردن نزدیک با مراجعین انرژی زیادی دارم.',
    'در این کار دستاوردهای ارزشمندی داشته‌ام.',
    'احساس می‌کنم در انتهای توانم هستم.',
    'در کارم با مسائل عاطفی آرامش دارم.',
    'احساس می‌کنم مراجعین/همکارانم مرا برای برخی مشکلاتشان سرزنش می‌کنند.'
];

const SCALE_LABELS = [
    { num: 0, full: 'هرگز',            short: 'هرگز' },
    { num: 1, full: 'چند بار در سال',  short: 'چند بار در سال' },
    { num: 2, full: 'ماهی یک بار',     short: 'ماهی یک بار' },
    { num: 3, full: 'چند بار در ماه',  short: 'چند بار در ماه' },
    { num: 4, full: 'هفته‌ای یک بار',  short: 'هفته‌ای یک بار' },
    { num: 5, full: 'چند بار در هفته', short: 'چند بار در هفته' },
    { num: 6, full: 'هر روز',          short: 'هر روز' }
];

let responses = new Array(22).fill(null);

function updateProgress() {
    const answered = responses.filter(r => r !== null).length;
    const pct = Math.round((answered / 22) * 100);

    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressLabel').textContent = `${answered} از ۲۲ سؤال پاسخ داده شد`;
    document.getElementById('progressWrap').style.display = 'block';

    const allDone = answered === 22;
    document.getElementById('submitArea').style.display = 'block';
    document.getElementById('btnSubmit').disabled = !allDone;

    if (!allDone) {
        document.getElementById('btnSubmit').previousElementSibling.style.display = 'block';
    } else {
        document.getElementById('btnSubmit').previousElementSibling.style.display = 'none';
    }
}

function buildQuestions() {
    const list = document.getElementById('questionsList');
    list.innerHTML = '';

    MBI_QUESTIONS.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'question-card';
        card.id = `qcard-${idx}`;

        const legendItems = SCALE_LABELS.map(s =>
            `<div class="scale-legend-item">
                <span class="scale-legend-num">${s.num}</span>
                <span class="scale-legend-text">${s.full}</span>
             </div>`
        ).join('');

        const buttons = SCALE_LABELS.map(s =>
            `<button class="likert-btn" data-q="${idx}" data-val="${s.num}">
                <span class="likert-label">${s.short}</span>
             </button>`
        ).join('');

        card.innerHTML = `
            <div class="question-number">سؤال ${idx + 1} از ۲۲</div>
            <div class="question-text">${q}</div>
            <div class="likert-scale">${buttons}</div>`;

        list.appendChild(card);
    });

    list.addEventListener('click', e => {
        const btn = e.target.closest('.likert-btn');
        if (!btn) return;

        const q = parseInt(btn.dataset.q);
        const val = parseInt(btn.dataset.val);

        responses[q] = val;

        const card = document.getElementById(`qcard-${q}`);
        card.classList.add('answered');
        card.querySelectorAll('.likert-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');

        updateProgress();

        // Auto-scroll to next question
        const nextCard = document.getElementById(`qcard-${q + 1}`);
        if (nextCard) {
            setTimeout(() => {
                nextCard.scrollIntoView({behavior: 'smooth', block: 'center'});
            }, 200);
        }
    });
}

function levelFa(level) {
    return {low: 'پایین', moderate: 'متوسط', high: 'بالا'}[level] || level;
}

function renderResults(scores) {
    document.getElementById('questionsSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('mainIntro').style.display = 'none';

    const grid = document.getElementById('subscaleGrid');
    const subscales = [
        {key: 'ee', label: 'خستگی عاطفی', barClass: 'bar-ee', note: '(کمتر = بهتر)'},
        {key: 'dp', label: 'مسخ شخصیت', barClass: 'bar-dp', note: '(کمتر = بهتر)'},
        {key: 'pa', label: 'کفایت فردی', barClass: 'bar-pa', note: '(بیشتر = بهتر)'}
    ];

    grid.innerHTML = subscales.map(s => {
        const d = scores[s.key];
        const pct = Math.round((d.score / d.max) * 100);
        return `
        <div class="subscale-item">
            <div class="subscale-label">${s.label} <span style="font-size:0.72rem;opacity:0.7">${s.note}</span></div>
            <div class="subscale-score">${d.score} <span style="font-size:0.9rem;color:var(--text-muted)">/ ${d.max}</span></div>
            <span class="subscale-level level-${d.level}">${levelFa(d.level)}</span>
            <div class="subscale-bar-wrap">
                <div class="subscale-bar-fill ${s.barClass}" style="width:${pct}%"></div>
            </div>
        </div>`;
    }).join('');

    document.getElementById('feedbackBox').innerHTML =
        '<strong>تفسیر:</strong> ' + scores.feedback;

    window.scrollTo({top: 0, behavior: 'smooth'});
}

async function submitAssessment() {
    const btn = document.getElementById('btnSubmit');
    btn.disabled = true;
    btn.textContent = 'در حال پردازش...';

    try {
        const res = await fetch('/api/assessment/submit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({responses})
        });
        const data = await res.json();

        if (!res.ok) {
            alert(data.message || 'خطا در ارسال. لطفاً دوباره امتحان کنید.');
            btn.disabled = false;
            btn.textContent = 'مشاهده نتایج';
            return;
        }

        renderResults(data.scores);

        const ebookModal = document.getElementById('ebookModal');
        if (ebookModal) {
            setTimeout(() => ebookModal.classList.remove('hidden'), 10000);
        }

    } catch (e) {
        alert('خطا در اتصال به سرور');
        btn.disabled = false;
        btn.textContent = 'مشاهده نتایج';
    }
}

async function submitLead(e) {
    e.preventDefault();

    const errorBox = document.getElementById('leadGateError');
    const name = document.getElementById('leadName').value.trim();
    const email = document.getElementById('leadEmail').value.trim();
    const phone = document.getElementById('leadPhone').value.trim();

    errorBox.classList.add('hidden');

    if (!name) {
        errorBox.textContent = 'نام و نام خانوادگی الزامی است';
        errorBox.classList.remove('hidden');
        return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errorBox.textContent = 'ایمیل معتبر نیست';
        errorBox.classList.remove('hidden');
        return;
    }
    if (!/^09\d{9}$/.test(phone)) {
        errorBox.textContent = 'شماره موبایل معتبر نیست';
        errorBox.classList.remove('hidden');
        return;
    }

    const btn = document.getElementById('btnLeadSubmit');
    btn.disabled = true;
    btn.textContent = 'در حال ثبت...';

    try {
        const res = await fetch('/api/assessment/lead', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, email, phone})
        });
        const data = await res.json();

        if (!res.ok) {
            errorBox.textContent = data.message || 'خطا در ثبت اطلاعات. لطفاً دوباره امتحان کنید.';
            errorBox.classList.remove('hidden');
            btn.disabled = false;
            btn.textContent = 'شروع پرسشنامه';
            return;
        }

        document.getElementById('leadGateSection').style.display = 'none';
        document.getElementById('mainIntro').style.display = 'block';
        document.getElementById('questionsSection').style.display = 'block';
        buildQuestions();
        window.scrollTo({top: 0, behavior: 'smooth'});

    } catch (e) {
        errorBox.textContent = 'خطا در اتصال به سرور';
        errorBox.classList.remove('hidden');
        btn.disabled = false;
        btn.textContent = 'شروع پرسشنامه';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('leadGateForm').addEventListener('submit', submitLead);

    document.getElementById('btnSubmit').addEventListener('click', submitAssessment);

    const btnSkipEbook = document.getElementById('btnSkipEbook');
    if (btnSkipEbook) {
        btnSkipEbook.addEventListener('click', () => {
            document.getElementById('ebookModal').classList.add('hidden');
        });
    }

    document.getElementById('btnRetake').addEventListener('click', () => {
        responses = new Array(22).fill(null);
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('questionsSection').style.display = 'block';
        document.getElementById('mainIntro').style.display = 'block';
        buildQuestions();
        document.getElementById('progressFill').style.width = '0%';
        document.getElementById('progressLabel').textContent = '';
        document.getElementById('submitArea').style.display = 'none';
        window.scrollTo({top: 0, behavior: 'smooth'});
    });
});
