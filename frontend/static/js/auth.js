'use strict';

const Auth = (() => {
    let currentPhone = '';
    let timerInterval = null;
    let timerSeconds = 300;

    const modal   = document.getElementById('authModal');
    const stepPhone = document.getElementById('stepPhone');
    const stepOtp   = document.getElementById('stepOtp');
    const phoneInput = document.getElementById('phoneInput');
    const otpInput   = document.getElementById('otpInput');
    const phoneError = document.getElementById('phoneError');
    const otpError   = document.getElementById('otpError');
    const otpDisplay = document.getElementById('otpDisplayBox');
    const otpSentTo  = document.getElementById('otpSentTo');
    const timerEl    = document.getElementById('timerCount');
    const timerLabel = document.getElementById('otpTimer');
    const btnRequest  = document.getElementById('btnRequestOtp');
    const btnVerify   = document.getElementById('btnVerifyOtp');
    const btnResend   = document.getElementById('btnResendOtp');
    const btnChange   = document.getElementById('btnChangePhone');

    function showError(el, msg) {
        el.textContent = msg;
        el.classList.remove('hidden');
    }

    function hideError(el) {
        el.classList.add('hidden');
    }

    function setLoading(btn, loading) {
        btn.disabled = loading;
        btn.innerHTML = loading
            ? '<span class="spinner"></span>'
            : btn.dataset.label;
    }

    function startTimer() {
        timerSeconds = 300;
        clearInterval(timerInterval);
        btnResend.classList.add('hidden');
        timerLabel.classList.remove('expired');

        timerInterval = setInterval(() => {
            timerSeconds--;
            const m = Math.floor(timerSeconds / 60);
            const s = timerSeconds % 60;
            timerEl.textContent = `${m}:${s.toString().padStart(2, '0')}`;

            if (timerSeconds <= 0) {
                clearInterval(timerInterval);
                timerLabel.classList.add('expired');
                timerEl.textContent = '0:00';
                btnResend.classList.remove('hidden');
            }
        }, 1000);
    }

    async function requestOtp() {
        const phone = phoneInput.value.trim();
        hideError(phoneError);

        if (!/^09\d{9}$/.test(phone)) {
            showError(phoneError, 'شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود');
            return;
        }

        btnRequest.dataset.label = btnRequest.innerHTML;
        setLoading(btnRequest, true);

        try {
            const res = await fetch('/api/auth/request-otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone_number: phone})
            });
            const data = await res.json();

            if (!res.ok) {
                showError(phoneError, data.message || 'خطا در ارسال کد');
                return;
            }

            currentPhone = phone;
            otpSentTo.textContent = `کد به ${phone} ارسال شد`;

            if (data.display_otp) {
                otpDisplay.textContent = data.display_otp;
                otpDisplay.classList.remove('hidden');
            } else {
                otpDisplay.classList.add('hidden');
            }

            stepPhone.classList.add('hidden');
            stepOtp.classList.remove('hidden');
            otpInput.focus();
            startTimer();

        } catch (e) {
            showError(phoneError, 'خطا در اتصال به سرور');
        } finally {
            setLoading(btnRequest, false);
            btnRequest.innerHTML = btnRequest.dataset.label;
        }
    }

    async function verifyOtp() {
        const code = otpInput.value.trim();
        hideError(otpError);

        if (!code || code.length < 4) {
            showError(otpError, 'کد تأیید را وارد کنید');
            return;
        }

        btnVerify.dataset.label = btnVerify.innerHTML;
        setLoading(btnVerify, true);

        try {
            const res = await fetch('/api/auth/verify-otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone_number: currentPhone, otp_code: code})
            });
            const data = await res.json();

            if (!res.ok) {
                showError(otpError, data.message || 'کد اشتباه است');
                return;
            }

            clearInterval(timerInterval);
            modal.classList.add('hidden');
            Chat.onAuthSuccess();

        } catch (e) {
            showError(otpError, 'خطا در اتصال به سرور');
        } finally {
            setLoading(btnVerify, false);
            btnVerify.innerHTML = btnVerify.dataset.label;
        }
    }

    async function checkStatus() {
        try {
            const res = await fetch('/api/auth/status');
            const data = await res.json();
            if (data.logged_in) {
                modal.classList.add('hidden');
                Chat.onAuthSuccess();
            }
        } catch (e) {
            // show modal
        }
    }

    function init() {
        btnRequest.addEventListener('click', requestOtp);
        btnVerify.addEventListener('click', verifyOtp);

        btnResend.addEventListener('click', () => {
            stepOtp.classList.add('hidden');
            stepPhone.classList.remove('hidden');
            otpInput.value = '';
            hideError(otpError);
            otpDisplay.classList.add('hidden');
        });

        btnChange.addEventListener('click', () => {
            stepOtp.classList.add('hidden');
            stepPhone.classList.remove('hidden');
            otpInput.value = '';
            hideError(otpError);
            otpDisplay.classList.add('hidden');
            clearInterval(timerInterval);
        });

        phoneInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') requestOtp();
        });

        otpInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') verifyOtp();
        });

        checkStatus();
    }

    return {init};
})();

document.addEventListener('DOMContentLoaded', Auth.init);
