'use strict';

const WAAQ_QUESTIONS = [
    'من با وجود داشتن افکار و احساسات منفی در مورد کارم، وظایفم را با موفقیت انجام می‌دهم.',
    'من می‌توانم به اهداف کاری‌ام برسم، حتی اگر نسبت به کارم دچار تردید شوم.',
    'من می‌توانم با وجود نگرانی‌هایی که دارم، برای انجام کارم به‌طور مؤثر برنامه‌ریزی کنم.',
    'وقتی افکار و احساسات منفی درباره کارم به سراغم می‌آید، باز هم می‌توانم به کارهایی که باید انجام شوند، تعهد داشته باشم.',
    'من به دلیل داشتن افکار و احساسات منفی، کارم را به تعویق نمی‌اندازم.',
    'من با وجود نگرانی‌هایی که دارم، کارهایم را به‌خوبی اجرا می‌کنم.',
    'من می‌توانم با وجود داشتن افکار منفی درباره کارم، به وظایف شغلی‌ام ادامه دهم.'
];

// No reverse-scored items — all items are direct scoring

const SCALE_LABELS = [
    { num: 1, full: 'هرگز درست نیست',  short: 'هرگز' },
    { num: 2, full: 'به‌ندرت درست است', short: 'به‌ندرت' },
    { num: 3, full: 'گاهی درست است', short: 'گاهی' },
    { num: 4, full: 'تاحدودی درست است', short: 'تاحدودی' },
    { num: 5, full: 'بیشتر اوقات درست است', short: 'بیشتر اوقات' },
    { num: 6, full: 'تقریباً همیشه درست است', short: 'تقریباً همیشه' },
    { num: 7, full: 'همیشه درست است', short: 'همیشه' }
];

const WAAQ_QUESTIONS_COUNT = 7;

let responses = new Array(WAAQ_QUESTIONS_COUNT).fill(null);

function updateProgress() {
    const answered = responses.filter(r => r !== null).length;
    const pct = Math.round((answered / WAAQ_QUESTIONS_COUNT) * 100);

    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressLabel').textContent = `${answered} از ${WAAQ_QUESTIONS_COUNT} سؤال پاسخ داده شد`;
    document.getElementById('progressWrap').style.display = 'block';

    const allDone = answered === WAAQ_QUESTIONS_COUNT;
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

    WAAQ_QUESTIONS.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'question-card';
        card.id = `qcard-${idx}`;

        const buttons = SCALE_LABELS.map(s =>
            `<button class="likert-btn" data-q="${idx}" data-val="${s.num}">
                <span class="likert-num">${s.num}</span>
                <span class="likert-label">${s.short}</span>
             </button>`
        ).join('');

        card.innerHTML = `
            <div class="question-number">سؤال ${idx + 1} از ${WAAQ_QUESTIONS_COUNT}</div>
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

function classifyWaaq(totalScore) {
    if (totalScore >= 7 && totalScore <= 26) return 'low';
    if (totalScore >= 27 && totalScore <= 39) return 'moderate';
    return 'high';
}

function getFeedback(level) {
    const messages = {
        low: 'انعطاف‌پذیری روانی پایین: نشان‌دهنده اجتناب تجربی بالا در محیط کار است. شما در مواجهه با استرس‌ها و افکار منفی، عملکرد کاری خود را از دست می‌دهید یا دچار فرسودگی می‌شوید.',
        moderate: 'انعطاف‌پذیری روانی متوسط: نشان می‌دهد تا حدودی می‌توانید وظایفتان را پیش ببرید، اما در موقعیت‌های بسیار چالش‌برانگیز ممکن است دچار توقف یا افت عملکرد شوید.',
        high: 'انعطاف‌پذیری روانی بالا: نشان‌دهنده مهارت عالی در پذیرش و عمل است. شما علی‌رغم وجود چالش‌ها، اضطراب‌ها یا افکار ناخوشایند شغلی، تمرکز و کارایی خود را کاملاً حفظ می‌کنید و به اهداف کاری‌تان متعهد می‌مانید.'
    };
    return messages[level] || '';
}

function levelFa(level) {
    return {low: 'پایین', moderate: 'متوسط', high: 'بالا'}[level] || level;
}

function renderResults(scores) {
    document.getElementById('questionsSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('mainIntro').style.display = 'none';

    const totalScore = scores.total_score;
    const level = scores.level;

    document.getElementById('totalScore').textContent = totalScore;

    const badgeContainer = document.getElementById('levelBadgeContainer');
    badgeContainer.innerHTML = `<span class="level-badge level-${level}">${levelFa(level)}</span>`;

    const pct = Math.round((totalScore / 49) * 100);
    document.getElementById('scoreBarFill').style.width = pct + '%';

    document.getElementById('feedbackBox').innerHTML =
        '<strong>تفسیر:</strong> ' + getFeedback(level);

    window.scrollTo({top: 0, behavior: 'smooth'});

    // Show ebook promo popup after 10 seconds
    const ebookModal = document.getElementById('ebookModal');
    if (ebookModal) {
        setTimeout(() => ebookModal.classList.remove('hidden'), 10000);
    }
}

async function submitAssessment() {
    const btn = document.getElementById('btnSubmit');
    btn.disabled = true;
    btn.textContent = 'در حال پردازش...';

    try {
        const res = await fetch('/api/waaq/submit', {
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
        responses = new Array(WAAQ_QUESTIONS_COUNT).fill(null);
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