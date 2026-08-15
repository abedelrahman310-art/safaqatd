from django.db import models
from django.conf import settings
from apps.procurement.models import Tender, Bid


class GeneratedRFP(models.Model):
    """
    مسودة دفتر الشروط المولدة آلياً بواسطة الذكاء الاصطناعي للمصلحة المتعاقدة
    """
    SECTOR_CHOICES = [
        ('works', 'أشغال وبناء وبنية تحتية'),
        ('supplies', 'اقتناء لوازم ومعدات وتجهيزات'),
        ('studies', 'دراسات واستشارات هندسية وتقنية'),
        ('services', 'خدمات وصيانة وحراسة'),
    ]

    PROCEDURE_TYPE_CHOICES = [
        ('open_tender', 'طلب عروض مفتوح مع اشتراط قدرات دنيا'),
        ('restricted_tender', 'طلب عروض محدود'),
        ('consultation', 'استشارة بسيطة (صفقة أقل من العتبة)'),
        ('direct_negotiation', 'تراضي بعد الاستشارة'),
    ]

    authority = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generated_rfps', verbose_name='المصلحة المتعاقدة')
    project_title = models.CharField(max_length=255, verbose_name='عنوان موضوع المشروع')
    sector = models.CharField(max_length=20, choices=SECTOR_CHOICES, default='works', verbose_name='قطاع الصفقة')
    procedure_type = models.CharField(max_length=30, choices=PROCEDURE_TYPE_CHOICES, default='open_tender', verbose_name='طبيعة الإجراء القانوني')
    estimated_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='الميزانية التقديرية (دج)')
    execution_duration_months = models.IntegerField(default=6, verbose_name='مدة الإنجاز المقترحة (أشهر)')
    
    # المحتويات المولدة
    administrative_conditions = models.TextField(verbose_name='الشروط الإدارية والتأهيلية')
    technical_specs = models.TextField(verbose_name='المواصفات التقنية القياسية')
    scoring_criteria = models.JSONField(default=dict, verbose_name='سلم التنقيط والتقييم التقني (100 نقطة)')
    required_documents = models.JSONField(default=list, verbose_name='قائمة الوثائق الإلزامية المطلوبة')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التوليد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ آخر تعديل')

    class Meta:
        verbose_name = 'مسودة دفتر شروط ذكية'
        verbose_name_plural = 'مسودات دفاتر الشروط الذكية'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project_title} ({self.get_sector_display()})"


class AutomatedEvaluationSession(models.Model):
    """
    جلسة تقييم وتفريغ العروض آلياً للجنة فتح وتقييم العروض
    """
    tender = models.OneToOneField(Tender, on_delete=models.CASCADE, related_name='ai_evaluation_session', verbose_name='الصفقة المعنية')
    conducted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='المشرف على الجلسة')
    evaluation_summary = models.JSONField(default=dict, verbose_name='نتائج التقييم المقارن والتنقيط')
    recommended_bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_recommended_award', verbose_name='العرض الموصى به للترسية')
    arithmetic_errors_found = models.BooleanField(default=False, verbose_name='تم رصد أخطاء حسابية في العروض')
    notes = models.TextField(blank=True, verbose_name='ملاحظات ومحضر التقييم الآلي')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ جلسة التقييم')

    class Meta:
        verbose_name = 'جلسة تقييم عروض آلية'
        verbose_name_plural = 'جلسات تقييم العروض الآلية'

    def __str__(self):
        return f"تقييم عروض الصفقة #{self.tender.id}: {self.tender.title[:30]}"


class PriceBenchmarkEstimate(models.Model):
    """
    تقدير الميزانية والأسعار المرجعية العادلة لمشروع بناءً على بيانات السوق
    """
    project_title = models.CharField(max_length=255, verbose_name='موضوع المشروع أو الخدمة')
    sector = models.CharField(max_length=50, verbose_name='القطاع')
    estimated_min_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='الحد الأدنى العادل (دج)')
    estimated_avg_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر المرجعي المتوقع (دج)')
    estimated_max_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='الحد الأعلى التقديري (دج)')
    confidence_level = models.CharField(max_length=20, default='عالية (88%)', verbose_name='مستوى الثقة الإحصائية')
    market_factors = models.JSONField(default=list, verbose_name='عوامل تسعير السوق التاريخية')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التقدير')

    class Meta:
        verbose_name = 'تقدير سعر مرجعي'
        verbose_name_plural = 'تقديرات الأسعار المرجعية'

    def __str__(self):
        return f"{self.project_title} - {self.estimated_avg_price} دج"
