#!/usr/bin/env bash
# Render Build Script for صفقات ذكية
set -o errexit

echo "========================================="
echo "  بناء منصة صفقات ذكية"
echo "========================================="

echo "→ تثبيت المكتبات..."
pip install --upgrade pip
pip install -r requirements.txt

echo "→ جمع الملفات الثابتة..."
python manage.py collectstatic --no-input

echo "→ تنفيذ ترحيلات قاعدة البيانات..."
python manage.py migrate --no-input

echo "========================================="
echo "  ✓ تم البناء بنجاح"
echo "========================================="
