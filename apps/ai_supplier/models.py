from django.db import models
from django.conf import settings
from apps.procurement.models import Tender, Bid


class SupplierMatchScore(models.Model):
    """
    سجل درجات مطابقة الصفقات لكل متعامل اقتصادي
    """
    supplier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='match_scores', verbose_name='المتعامل الاقتصادي')
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='supplier_matches', verbose_name='الصفقة')
    overall_match_score = models.IntegerField(default=75, verbose_name='درجة الملاءمة الإجمالية (0-100)')
    sector_match = models.IntegerField(default=80, verbose_name='تطابق التخصص والنشاط')
    capacity_match = models.IntegerField(default=70, verbose_name='تطابق التصنيف والقدرة المالية')
    match_reasons = models.JSONField(default=list, verbose_name='أسباب ودوافع التوصية')
    is_dismissed = models.BooleanField(default=False, verbose_name='تم إخفاؤها من طرف المورد')
    evaluated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ احتساب المطابقة')

    class Meta:
        verbose_name = 'درجة مطابقة صفقة لمورد'
        verbose_name_plural = 'درجات مطابقة الصفقات للموردين'
        ordering = ['-overall_match_score']
        unique_together = ('supplier', 'tender')

    def __str__(self):
        return f"{self.supplier.username} - {self.tender.title[:30]} ({self.overall_match_score}%)"


class TenderSummaryAI(models.Model):
    """
    الملخص الذكي لدفتر الشروط الموجه للمتعامل الاقتصادي
    """
    tender = models.OneToOneField(Tender, on_delete=models.CASCADE, related_name='ai_summary', verbose_name='الصفقة')
    key_deadlines = models.JSONField(default=dict, verbose_name='المهل والآجال الزمنية الجوهرية')
    financial_guarantees = models.CharField(max_length=255, default='كفالة تعهد بنسبة 1% من قيمة العرض', verbose_name='الكفالات والضمانات البنكية')
    mandatory_qualifications = models.JSONField(default=list, verbose_name='شروط التأهيل الإلزامية')
    scoring_highlights = models.JSONField(default=dict, verbose_name='أبرز محاور سلم التنقيط')
    potential_risks = models.JSONField(default=list, verbose_name='التنبيهات والمحاذير التعاقدية')
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ توليد الملخص')

    class Meta:
        verbose_name = 'ملخص دفتر الشروط الذكي'
        verbose_name_plural = 'ملخصات دفاتر الشروط الذكية'

    def __str__(self):
        return f"ملخص دفتر شروط: {self.tender.title[:30]}"


class BidReadinessReport(models.Model):
    """
    تقرير الفحص المسبق لجاهزية ملف العرض وتفادي الإقصاء الإداري
    """
    supplier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='المتعامل الاقتصادي')
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, verbose_name='الصفقة')
    readiness_percentage = models.IntegerField(default=85, verbose_name='نسبة اكتمال وجاهزية الملف')
    missing_documents = models.JSONField(default=list, verbose_name='الوثائق الناقصة أو المنتهية الصلاحية')
    valid_documents = models.JSONField(default=list, verbose_name='الوثائق المستوفاة والصحيحة')
    compliance_verdict = models.CharField(max_length=50, default='جاهز للإيداع بعد استكمال وثيقة واحدة', verbose_name='القرار الإرشادي')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الفحص')

    class Meta:
        verbose_name = 'تقرير جاهزية العرض'
        verbose_name_plural = 'تقارير جاهزية العروض'

    def __str__(self):
        return f"جاهزية عرض {self.supplier.username} للصفقة #{self.tender.id} ({self.readiness_percentage}%)"
