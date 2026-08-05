from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('authority', 'مصلحة متعاقدة'),
        ('supplier', 'متعامل اقتصادي'),
        ('central_admin', 'إدارة مركزية'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        permissions = [
            ("view_central_dashboard", "Can view central administration dashboard"),
            ("manage_all_users", "Can manage all users and suppliers"),
            ("audit_all_tenders", "Can audit all tenders system-wide"),
            ("view_system_reports", "Can view system-wide reports"),
        ]
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="الاسم الكامل")
    wilaya = models.CharField(max_length=100, blank=True, null=True, verbose_name="الولاية")
    
    # Supplier fields
    national_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="بطاقة التعريف الوطني")
    commercial_register = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم السجل التجاري")
    company_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="نوع الشركة")
    commercial_register_doc = models.FileField(upload_to='suppliers/rc/', null=True, blank=True, verbose_name="نسخة السجل التجاري (PDF)")
    tax_card_doc = models.FileField(upload_to='suppliers/tax/', null=True, blank=True, verbose_name="نسخة البطاقة الجبائية (PDF)")
    
    # Authority fields
    institution_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="التسمية الرسمية للمصلحة")
    sector = models.CharField(max_length=255, blank=True, null=True, verbose_name="القطاع الوصي")
    
    # Blacklist fields (for suppliers)
    is_blacklisted = models.BooleanField(default=False, verbose_name="مدرج في القائمة السوداء")
    blacklist_reason = models.TextField(blank=True, null=True, verbose_name="سبب الإدراج في القائمة السوداء")
    blacklist_until = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ انتهاء الحظر")

    @property
    def display_name(self):
        if self.role == 'authority' and self.institution_name:
            return self.institution_name
        return self.full_name or self.username

    def __str__(self):
        return self.email or self.username
