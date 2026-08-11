# دليل نشر منصة صفقات ذكية على Render

## المتطلبات المسبقة
- حساب على [GitHub](https://github.com) مع مستودع (Repository) يحتوي على كود المشروع.
- حساب على [Render.com](https://render.com) (مجاني).

---

## الخطوة 1: رفع الكود إلى GitHub

```bash
git add .
git commit -m "تهيئة المنصة للنشر على Render"
git push origin main
```

> إذا لم تربط مستودعاً بعد:
> ```bash
> git remote add origin https://github.com/<username>/<repo-name>.git
> git push -u origin main
> ```

---

## الخطوة 2: إنشاء الخدمات على Render

### الطريقة الأولى: Blueprint (مُوصى بها)
1. سجّل الدخول إلى [Render Dashboard](https://dashboard.render.com).
2. اضغط **New** → **Blueprint**.
3. اختر المستودع من GitHub واضغط **Connect**.
4. سيقرأ Render ملف `render.yaml` تلقائياً ويعرض لك قائمة الموارد:
   - **safakat-db**: قاعدة بيانات PostgreSQL.
   - **safakat-web**: خدمة الويب (Gunicorn).
5. اضغط **Apply** لبدء البناء.

### الطريقة الثانية: إنشاء يدوي
1. أنشئ **PostgreSQL** مجاني من Render Dashboard.
2. أنشئ **Web Service** جديد:
   - **Build Command**: `./build.sh`
   - **Start Command**: `./start.sh`
3. أضف متغيرات البيئة يدوياً (انظر القسم التالي).

---

## الخطوة 3: ضبط متغيرات البيئة (Environment Variables)

المتغيرات التالية يجب ضبطها في لوحة تحكم Render ← **Environment**:

| المتغير | القيمة | ملاحظات |
|---------|--------|---------|
| `DATABASE_URL` | يُعبأ تلقائياً عبر Blueprint | رابط PostgreSQL |
| `SECRET_KEY` | يُولّد تلقائياً عبر Blueprint | مفتاح التشفير |
| `DEBUG` | `False` | **لا تغيّره إلى True أبداً في الإنتاج** |
| `ALLOWED_HOSTS` | `.onrender.com` | أو اسم الدومين الخاص بك |
| `CSRF_TRUSTED_ORIGINS` | `https://safakat-web.onrender.com` | عدّله إذا كان لديك دومين مخصص |
| `ENCRYPTION_KEY` | (أنشئ مفتاحاً آمناً) | مفتاح تشفير الملفات الحساسة |
| `GEMINI_API_KEY` | (اختياري) | مفتاح API لخدمة Gemini AI |

### لتوليد ENCRYPTION_KEY آمن:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

---

## الخطوة 4: ما بعد النشر

### إنشاء حساب المسؤول الأول
بعد نجاح البناء، افتح **Shell** من Render Dashboard:
```bash
python manage.py createsuperuser
```

### إنشاء حساب مراقب (Regulator)
```bash
python manage.py shell
```
ثم:
```python
from apps.accounts.models import User
user = User.objects.create_user(
    username='regulator1',
    email='regulator@example.com',
    password='كلمة_مرور_قوية',
    role='central_admin'
)
# الصلاحيات ستُمنح تلقائياً عبر نظام Signals
```

---

## الخطوة 5: التحقق من النشر
1. افتح الرابط: `https://safakat-web.onrender.com`
2. تأكد من ظهور صفحة تسجيل الدخول.
3. سجّل دخول بحساب المراقب وتصفح اللوحة المركزية.

---

## ملاحظات هامة

> **⚠️ الخطة المجانية في Render:**
> - الخادم ينام بعد 15 دقيقة من عدم الاستخدام (أول طلب بعدها يأخذ ~30 ثانية).
> - قاعدة البيانات المجانية تنتهي بعد 90 يوماً.
> - لا يوجد Redis مجاني — مهام Celery معطلة مؤقتاً.

> **🔒 أمان:**
> - `SECRET_KEY` يُولّد تلقائياً ولا يُشارك.
> - `DEBUG = False` دائماً في الإنتاج.
> - الملفات الحساسة (العروض المشفرة) لا يمكن الوصول إليها مباشرة عبر URL.

---

## التحديثات المستقبلية
أي تعديل ترفعه إلى GitHub عبر `git push` سيقوم Render بإعادة بناء المنصة وتحديثها أوتوماتيكياً خلال 2-5 دقائق.
