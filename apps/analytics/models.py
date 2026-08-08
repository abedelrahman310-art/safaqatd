from django.db import models
from django.conf import settings

class SmartAlert(models.Model):
    SEVERITY_CHOICES = (
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
        ('critical', 'حرج'),
    )

    title = models.CharField(max_length=255, verbose_name="عنوان التنبيه")
    description = models.TextField(verbose_name="التفاصيل")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', verbose_name="درجة الأهمية")
    alert_type = models.CharField(max_length=100, verbose_name="نوع التنبيه", help_text="مثال: تأخير، بيانات ناقصة")
    related_tender = models.ForeignKey('procurement.Tender', on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts', verbose_name="الصفقة المرتبطة")
    suggested_action = models.TextField(blank=True, null=True, verbose_name="الإجراء المقترح")
    
    is_resolved = models.BooleanField(default=False, verbose_name="تمت المراجعة")
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts', verbose_name="تمت المراجعة بواسطة")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ المراجعة")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الاكتشاف")

    class Meta:
        verbose_name = "تنبيه ذكي"
        verbose_name_plural = "التنبيهات الذكية"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class DataQualityIssue(models.Model):
    ISSUE_TYPES = (
        ('missing_field', 'حقل ناقص'),
        ('invalid_date', 'تاريخ غير صحيح'),
        ('outlier_value', 'قيمة غير منطقية'),
        ('inconsistent_status', 'تعارض في الحالة'),
    )

    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPES, verbose_name="نوع المشكلة")
    description = models.TextField(verbose_name="وصف المشكلة")
    related_tender = models.ForeignKey('procurement.Tender', on_delete=models.CASCADE, related_name='data_issues', verbose_name="الصفقة المرتبطة")
    field_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="الحقل المعني")
    
    is_fixed = models.BooleanField(default=False, verbose_name="تم الحل")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مشكلة جودة بيانات"
        verbose_name_plural = "مشاكل جودة البيانات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_issue_type_display()} - {self.related_tender.title}"
