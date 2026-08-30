'use strict';

// گزینه‌ها: ۱=الف، ۲=ب، ۳=ج، ۴=د
const KNOT_LETTERS = ['الف', 'ب', 'ج', 'د'];

const KNOT_QUESTIONS = [
    {
        text: 'وقتی یک نفر مانند همکار، رقیب، یا حتی یک نفر در همان حوزه‌ی کاری، سریع‌تر یا بهتر از من کاری را انجام می‌دهد، اولین واکنش من این است:',
        options: [
            'حس می‌کنم باید بیشتر تلاش کنم تا جایگاهم را نگه دارم.',
            'حس می‌کنم دارم مسئولیت کارهای بیشتری را هم قبول می‌کنم تا عقب نمانم.',
            'دیگر برایم مهم نیست چه کسی سریع‌تر است.',
            'به این فکر می‌کنم که آیا اصلاً باید در این مسیر بمانم یا نه؟'
        ]
    },
    {
        text: 'وقتی از من می‌پرسند دقیقاً چه‌کاری انجام می‌دهم، این حس را دارم:',
        options: [
            'کارم روشن است، اما کنترلی روی چگونگی انجامش ندارم.',
            'کارم آن‌قدر گسترده شده که توضیحش سخت است.',
            'کارم را می‌دانم، فقط دیگر برایم اهمیتی ندارد.',
            'خودم هم دقیق نمی‌دانم دارم چه‌کار می‌کنم.'
        ]
    },
    {
        text: 'رابطه‌ام با کسانی که در کارم به آن‌ها وابسته‌ام (مشتری، شریک، سرمایه‌گذار، یا مدیر بالادستی)، بیشتر این‌طور است:',
        options: [
            'حس می‌کنم تصمیم‌های مهم بدون من گرفته می‌شود.',
            'حس می‌کنم کار آن‌ها هم روی دوش من افتاده است.',
            'دیگر برایم فرقی نمی‌کند تاییدم کنند یا نکنند.',
            'حس می‌کنم مسیرمان از هم جدا شده است.'
        ]
    },
    {
        text: 'وقتی به روزهای کاری‌ام فکر می‌کنم، این جمله به من نزدیک‌تر است:',
        options: [
            'هر روز حس می‌کنم باید نشان بدهم هنوز به‌اندازه‌ی کافی خوبم.',
            'هر روز باید به همه‌چیز و همه‌کس جواب بدهم.',
            'فقط دارم روزها را رد می‌کنم.',
            'مطمئن نیستم دارم به کجا می‌رسم.'
        ]
    },
    {
        text: 'اگر می‌توانستم همین حالا فقط یک چیز را در شرایط شغلی‌ام عوض کنم، این بود:',
        options: [
            'اختیار بیشتر روی تصمیم‌هایی که به من مربوط است.',
            'توانایی نه‌گفتن بدون احساس گناه.',
            'حس دوباره‌ی مهم‌بودن، درباره آنچه انجام می‌دهم.',
            'دانستن این‌که «قدم بعدیِ من دقیقاً چیست؟»'
        ]
    },
    {
        text: 'وقتی کسی روش کارم را زیر سوال می‌برد، بیشترین چیزی که در ذهنم می‌گذرد این است:',
        options: [
            'باید ثابت کنم هنوز بلدم.',
            'باز هم من باید توضیح بدهم، انگار مسئول همه‌چیزم.',
            'فرقی نمی‌کند چه بگویم.',
            'شاید اصلاً روش من دیگر جواب نمی‌دهد.'
        ]
    },
    {
        text: 'وقتی با خانواده یا دوستانم درباره‌ی کارم صحبت می‌کنم، بیشتر این جمله را می‌گویم:',
        options: [
            'باید مدام نشان بدهم که هنوز کارآمدم.',
            'وقت ندارم، همیشه یک نفر از من چیزی می‌خواهد.',
            'فرقی نمی‌کند، فقط انجامش می‌دهم.',
            'نمی‌دانم دارم چه‌کار می‌کنم.'
        ]
    },
    {
        text: 'اگر بخواهم مسیر شغلی آینده‌ام را توصیف کنم:',
        options: [
            'همین مسیر، فقط با اختیار و کنترل بیشتر.',
            'همین مسیر، فقط با مرزهای روشن‌تر.',
            'کاری که دوباره برایم معنا داشته باشد.',
            'مسیری با شکل کاملاً متفاوت از الان.'
        ]
    }
];

const KNOT_QUESTIONS_COUNT = 8;

let responses = new Array(KNOT_QUESTIONS_COUNT).fill(null);
let comments = new Array(KNOT_QUESTIONS_COUNT).fill('');

function updateProgress() {
    const answered = responses.filter(r => r !== null).length;
    const pct = Math.round((answered / KNOT_QUESTIONS_COUNT) * 100);

    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressLabel').textContent = `${answered} از ${KNOT_QUESTIONS_COUNT} سؤال پاسخ داده شد`;
    document.getElementById('progressWrap').style.display = 'block';

    const allDone = answered === KNOT_QUESTIONS_COUNT;
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

    KNOT_QUESTIONS.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'question-card';
        card.id = `qcard-${idx}`;

        const options = q.options.map((opt, oi) => `
            <button type="button" class="option-btn" data-q="${idx}" data-val="${oi + 1}">
                <span class="option-letter">${KNOT_LETTERS[oi]}</span>
                <span class="option-text">${opt}</span>
            </button>`).join('');

        card.innerHTML = `
            <div class="question-number">سؤال ${idx + 1} از ${KNOT_QUESTIONS_COUNT}</div>
            <div class="question-text">${q.text}</div>
            <div class="option-list">${options}</div>
            <div class="comment-area">
                <div class="comment-label">اگر می‌خواهید بیشتر توضیح دهید (اختیاری):</div>
                <textarea class="comment-input" data-q="${idx}" placeholder="توضیح شما (اختیاری)..."></textarea>
            </div>`;

        list.appendChild(card);
    });

    list.addEventListener('click', e => {
        const btn = e.target.closest('.option-btn');
        if (!btn) return;

        const q = parseInt(btn.dataset.q);
        const val = parseInt(btn.dataset.val);

        responses[q] = val;

        const card = document.getElementById(`qcard-${q}`);
        card.classList.add('answered');
        card.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
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

    list.addEventListener('input', e => {
        const area = e.target.closest('.comment-input');
        if (!area) return;
        comments[parseInt(area.dataset.q)] = area.value;
    });
}

function renderResults(scores) {
    const page = document.querySelector('.assessment-page');
    if (page) page.classList.add('results-mode');

    document.getElementById('questionsSection').style.display = 'none';
    document.getElementById('leadGateSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('mainIntro').style.display = 'none';

    // Profile badge
    document.getElementById('profileBadgeContainer').innerHTML =
        `<div class="profile-badge">پروفایل شما: ${scores.profile_title}</div>`;

    // Feedback paragraphs (lines starting with • are rendered as-is)
    const feedbackBox = document.getElementById('feedbackBox');
    feedbackBox.innerHTML = scores.body
        .split('\n')
        .filter(line => line.trim() !== '')
        .map(line => `<p>${line}</p>`)
        .join('');

    window.scrollTo({top: 0, behavior: 'auto'});

    // اطمینان از دیده‌شدن دکمه «ثبت نام در وبینار رایگان»
    setTimeout(() => {
        const cta = document.getElementById('webinarCta');
        if (cta) cta.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }, 300);

    // نمایش پاپ‌آپ پیشنهاد کتاب مدیر هوشمند، ۸ ثانیه پس از نمایش نتیجه
    if (typeof window.scheduleBookPromo === 'function') {
        window.scheduleBookPromo(8000);
    }
}

async function submitAssessment(btn) {
    btn = btn || document.getElementById('btnSubmit');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'در حال پردازش...';

    try {
        const res = await fetch('/api/knot/submit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                responses,
                comments: comments.map(c => c.trim())
            })
        });
        const data = await res.json();

        if (!res.ok) {
            alert(data.message || 'خطا در ارسال. لطفاً دوباره امتحان کنید.');
            btn.disabled = false;
            btn.textContent = originalText;
            return;
        }

        renderResults(data.scores);

    } catch (e) {
        alert('خطا در اتصال به سرور');
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function showLeadGate() {
    document.getElementById('submitArea').style.display = 'none';
    document.getElementById('leadGateSection').style.display = 'block';
    document.getElementById('leadGateSection').scrollIntoView({behavior: 'smooth', block: 'start'});
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
            btn.textContent = 'دریافت نتیجه';
            return;
        }

        // اطلاعات تماس ثبت شد؛ حالا نتیجه را محاسبه و نمایش می‌دهیم
        await submitAssessment(btn);

    } catch (e) {
        errorBox.textContent = 'خطا در اتصال به سرور';
        errorBox.classList.remove('hidden');
        btn.disabled = false;
        btn.textContent = 'دریافت نتیجه';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    buildQuestions();

    document.getElementById('leadGateForm').addEventListener('submit', submitLead);

    document.getElementById('btnSubmit').addEventListener('click', showLeadGate);
});
