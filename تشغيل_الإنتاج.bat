@echo off
echo ========================================================
echo جاري تشغيل منصة صفقات ذكية - بيئة الإنتاج (Production)
echo ========================================================

REM إعداد متغيرات بيئية وهمية مؤقتة للـ Build إذا لزم الأمر
set SECRET_KEY=production-secret-key-placeholder
set DATABASE_URL=postgres://safaqat_user:safaqat_secure_pass_2026@db:5432/safaqat_db
set ALLOWED_HOSTS=*

echo جاري بناء الحاويات الإنتاجية وتجهيز الملفات الثابتة (Static Files)...
docker-compose -f docker-compose.prod.yml build

echo.
echo جاري إطلاق المنصة في الخلفية...
docker-compose -f docker-compose.prod.yml up -d

echo.
echo ========================================================
echo اكتمل التشغيل بنجاح! المنصة الإنتاجية تعمل الآن.
echo للوصول إلى المنصة: http://localhost:8000
echo لإيقاف المنصة لاحقاً: docker-compose -f docker-compose.prod.yml down
echo ========================================================
pause
