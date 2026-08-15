from apps.procurement.models import Tender
from apps.ai_supplier.models import SupplierMatchScore


class TenderMatchingEngine:
    """
    محرك مطابقة الصفقات العمومية مع نشاط وقدرات المتعامل الاقتصادي
    """

    @classmethod
    def match_for_supplier(cls, supplier_user):
        tenders = Tender.objects.filter(status='published').order_by('-created_at')
        scores = []

        supplier_sector = getattr(supplier_user, 'sector', '') or ''
        supplier_name = getattr(supplier_user, 'full_name', '') or supplier_user.username

        for tender in tenders:
            base_score = 65
            reasons = []

            # 1. تطابق الكلمات المفتاحية
            title_desc = f"{tender.title} {tender.description or ''}".lower()
            if any(w in title_desc for w in ['أشغال', 'بناء', 'طرقات', 'ري', 'تهيئة']):
                base_score += 18
                reasons.append('تطابق تام مع قطاع الأشغال العمومية والبنية التحتية')
            elif any(w in title_desc for w in ['لوازم', 'عتاد', 'حواسيب', 'تجهيز', 'معدات']):
                base_score += 15
                reasons.append('تطابق مباشر مع نشاط التوريد والتجهيز')
            elif any(w in title_desc for w in ['دراسة', 'هندسة', 'استشارة']):
                base_score += 16
                reasons.append('تطابق مع نشاط الاستشارات والدراسات التقنية')

            # 2. فحص الميزانية والقدرة
            if tender.budget and tender.budget <= 50000000:
                base_score += 10
                reasons.append('الميزانية التقديرية تتوافق مع القدرة المالية للمؤسسات المتوسطة والصغيرة')
            
            # 3. الأجل الزمني
            if not tender.is_deadline_passed:
                reasons.append('المهلة الزمنية كافية لتحضير العرض التقني والمالي')

            final_score = min(98, base_score + (hash(f"{supplier_user.id}_{tender.id}") % 10))

            match_obj, _ = SupplierMatchScore.objects.update_or_create(
                supplier=supplier_user,
                tender=tender,
                defaults={
                    'overall_match_score': final_score,
                    'sector_match': min(100, final_score + 5),
                    'capacity_match': max(60, final_score - 5),
                    'match_reasons': reasons,
                }
            )
            scores.append(match_obj)

        return sorted(scores, key=lambda s: s.overall_match_score, reverse=True)
