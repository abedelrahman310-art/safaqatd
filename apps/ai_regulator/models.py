from django.db import models
from django.conf import settings
from apps.procurement.models import Tender, Bid


class CollusionAlert(models.Model):
    """
    سجل بلاغات وإنذارات التواطؤ وشبهات التنسيق المسبق بين العارضين
    """
    SEVERITY_CHOICES = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع / حرج'),
    ]

    ALERT_TYPE_CHOICES = [
        ('shared_ip', 'تطابق عنوان IP عند الإيداع'),
        ('shared_device', 'تطابق البصمة الرقمية للجهاز / المتصفح'),
        ('doc_metadata', 'تطابق ميتاداتا الوثائق والملفات المرفقة'),
        ('price_pattern', 'نمط تسعير مشبوه / عروض تغطية متبادلة'),
        ('submission_timing', 'تزامن مريب في توقيت الإيداع'),
    ]

    STATUS_CHOICES = [
        ('new', 'جديد قيد الفحص'),
        ('under_investigation', 'قيد التحقيق الرقابي'),
        ('confirmed', 'تم تأكيد الشبهة'),
        ('dismissed', 'تم الحفظ / مبرر قانونياً'),
    ]

    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='collusion_alerts', verbose_name='الصفقة المعنية')
    involved_suppliers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='collusion_flags', verbose_name='المتعاملون المشتبه بهم')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES, verbose_name='نوع الشبهة')
    severity = models.CharField(max_length=15, choices=SEVERITY_CHOICES, default='medium', verbose_name='درجة الخطورة')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='new', verbose_name='حالة البلاغ')
    risk_score = models.IntegerField(default=50, verbose_name='مؤشر المخاطر (0-100)')
    evidence_summary = models.TextField(verbose_name='ملخص القرائن والأدلة الرقمية')
    evidence_data = models.JSONField(default=dict, blank=True, verbose_name='البيانات التقنية التفصيلية')
    investigator_notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات المفتش المركزي')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرصد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'إنذار شبهة تواطؤ'
        verbose_name_plural = 'إنذارات شبهات التواطؤ'
        ordering = ['-risk_score', '-created_at']

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.get_alert_type_display()} - {self.tender.title[:30]}"


class RFPAuditReport(models.Model):
    """
    تقرير التدقيق الآلي لدفتر الشروط والمواصفات (Smart RFP Audit)
    """
    STATUS_CHOICES = [
        ('compliant', 'مطابق للمعايير الوطنية'),
        ('warning', 'يتضمن قيوداً وشروطاً تتطلب المراجعة'),
        ('violating', 'يتضمن شروطاً تعجيزية / غير مطابقة للمرسوم 23-12'),
    ]

    tender = models.OneToOneField(Tender, on_delete=models.CASCADE, related_name='rfp_audit', verbose_name='الصفقة')
    compliance_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='compliant', verbose_name='حالة المطابقة')
    compliance_score = models.IntegerField(default=100, verbose_name='درجة الامتثال (0-100)')
    tailored_specs_detected = models.BooleanField(default=False, verbose_name='شبهة تفصيل مواصفات حصرية')
    findings = models.JSONField(default=list, blank=True, verbose_name='الملاحظات والثغرات المرصودة')
    recommendations = models.TextField(blank=True, verbose_name='توصيات لجنة الرقابة المركزية')
    audited_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الفحص الآلي')

    class Meta:
        verbose_name = 'تقرير تدقيق دفتر الشروط'
        verbose_name_plural = 'تقارير تدقيق دفاتر الشروط'

    def __str__(self):
        return f"تدقيق دفتر الشروط: {self.tender.title[:30]} ({self.compliance_score}%)"


class TenderRiskScore(models.Model):
    """
    بطاقة تقييم المخاطر الشاملة لكل صفقة وتوقع احتمالية التعثر
    """
    tender = models.OneToOneField(Tender, on_delete=models.CASCADE, related_name='ai_risk_score', verbose_name='الصفقة')
    overall_risk = models.IntegerField(default=10, verbose_name='معدل الخطر الإجمالي (0-100)')
    failure_probability = models.FloatField(default=0.05, verbose_name='احتمالية تعثر المشروع')
    abnormally_low_bid_risk = models.BooleanField(default=False, verbose_name='خطر عروض متدنية بشكل غير طبيعي')
    factors = models.JSONField(default=dict, blank=True, verbose_name='العوامل المؤثرة في المخاطر')
    last_evaluated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ آخر تقييم')

    class Meta:
        verbose_name = 'بطاقة مخاطر الصفقة'
        verbose_name_plural = 'بطاقات مخاطر الصفقات'

    def __str__(self):
        return f"مخاطر الصفقة #{self.tender.id}: {self.overall_risk}%"
