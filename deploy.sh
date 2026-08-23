#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# deploy.sh — به‌روزرسانی سایت سای‌باما روی سرور از گیت‌هاب
# استفاده:  bash deploy.sh
# ─────────────────────────────────────────────────────────────
set -e

SERVICE="psybama"      # نام سرویس systemd
BRANCH="master"        # برنچ اصلی

# مسیر پروژه را خودکار از فایل سرویس می‌خوانیم
APP_DIR="$(systemctl show "$SERVICE" -p WorkingDirectory --value)"
if [ -z "$APP_DIR" ]; then
    echo "خطا: WorkingDirectory در سرویس $SERVICE تنظیم نشده است."
    echo "مسیر پروژه را پیدا کنید و این خط را جایگزین کنید:"
    echo '  APP_DIR="/مسیر/پروژه"'
    exit 1
fi

cd "$APP_DIR"

echo "── [1/4] دریافت تغییرات از گیت‌هاب ──"
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "خطا: این پوشه به گیت‌هاب متصل نیست."
    echo "ابتدا اجرا کنید:  git remote add origin https://github.com/mrth1353-psybama/psybama.git"
    exit 1
fi
git pull origin "$BRANCH"

echo "── [2/4] نصب وابستگی‌ها ──"
pip3 install -q -r backend/requirements.txt

echo "── [3/4] ری‌استارت سرویس $SERVICE ──"
systemctl restart "$SERVICE"
sleep 2

echo "── [4/4] وضعیت سرویس ──"
systemctl status "$SERVICE" --no-pager -l | head -n 12

echo ""
echo "✔ به‌روزرسانی کامل شد — $APP_DIR"
