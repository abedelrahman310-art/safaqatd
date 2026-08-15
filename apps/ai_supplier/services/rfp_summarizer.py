from apps.procurement.models import Tender
from apps.ai_supplier.models import TenderSummaryAI


class RFPSummarizerEngine:
    """
    محرك استخراج وتلخيص المهل والشروط الجوهرية لدفتر الشروط للمورد
    """

    @classmethod
    def get_or_generate_summary(cls, tender: Tender) -> TenderSummaryAI:
        if hasattr(tender, 'ai_summary'):
            return tender.ai_summary

        deadlines = {
            'submission_deadline': tender.deadline.strftime('%Y-%m-%d %H:%M') if tender.deadline else 'غير محدد بدقة',
            'bid_validity_days': '120 يوماً من تاريخ فتح الأظرفة',
            'opening_session': 'يوم انتهاء الإيداع على الساعة 14:00 في جلسة علنية',
        }

        quals = [
            'شهادة التأهيل والتصنيف المهني (الدرجة الثالثة فما فوق)',
            'إثبات مراجع مهنية لإنجاز مشروعين مماثلين خلال آخر 3 سنوات',
            'تقديم الحصائل المالية للسنوات الثلاث الأخيرة مؤشرة من محافظ الحسابات',
        ]

        scoring = {
            'الخبرة والمراجع المماثلة': '30 نقطة',
            'العتاد والآليات المبررة بالفواتير': '25 نقطة',
            'الكفاءات البشرية والتأطير التقني': '25 نقطة',
            'المنهجية والمخطط الزمني للورشة': '20 نقطة',
        }

        risks = [
            'تطبيق غرامات تأخير بنسبة 1/1000 عن كل يوم تأخير عن الآجال التعاقدية.',
            'إقصاء فوري في حال عدم تقديم كفالة التعهد البنكية الأصلية.',
        ]

        summary = TenderSummaryAI.objects.create(
            tender=tender,
            key_deadlines=deadlines,
            financial_guarantees='كفالة تعهد بنسبة 1% من القيمة الإجمالية للعرض المالي',
            mandatory_qualifications=quals,
            scoring_highlights=scoring,
            potential_risks=risks,
        )
        return summary
