import re
from apps.procurement.models import Tender
from apps.ai_regulator.models import RFPAuditReport


class RFPAuditorEngine:
    """
    محرك الفحص الآلي الذكي لنصوص دفاتر الشروط والمواصفات
    """

    RESTRICTIVE_KEYWORDS = [
        ('علامة تجارية حصرية', 'تحديد علامات تجارية دون إدراج عبارة "أو ما يعادلها"', 25),
        ('سنة خبرة تعجيزية', 'اشتراط سنوات خبرة تفوق 15 سنة لمشاريع عادية مما يقيد المنافسة', 20),
        ('شرط توطين حصري', 'اشتراط مقر ولائي مسبق دون مبرر تقني جوهري', 15),
        ('شهادة اعتماد فردية', 'طلب شهادات ISO حصرية غير متناسبة مع طبيعة الصفقة', 15),
    ]

    @classmethod
    def audit_tender(cls, tender: Tender) -> RFPAuditReport:
        content = f"{tender.title} {tender.description or ''}"
        score = 100
        findings = []
        tailored_specs = False

        # فحص وجود علامات تجارية بدون عبارة "أو ما يعادلها"
        brands = ['سيسكو', 'cisco', 'مايكروسوفت', 'microsoft', 'ديل', 'dell', 'تويوتا', 'toyota', 'hp', 'اتش بي']
        for b in brands:
            if b in content.lower():
                if 'ما يعادل' not in content and 'équivalent' not in content.lower():
                    tailored_specs = True
                    score -= 20
                    findings.append({
                        'type': 'exclusive_brand',
                        'title': f'تم ذكر العلامة التجارية ({b}) دون النص على "أو ما يعادلها"',
                        'severity': 'high',
                        'clause': 'المواصفات التقنية',
                        'legal_ref': 'المادة 27 من المرسوم الرئاسي 23-12'
                    })

        # فحص الشروط العامة
        if 'أشغال' in tender.title or 'بناء' in tender.title:
            if tender.budget and tender.budget < 50000000 and 'خبرة 10 سنوات' in content:
                score -= 15
                findings.append({
                    'type': 'excessive_experience',
                    'title': 'اشتراط خبرة مفرطة مقارنة بحجم الميزانية التقديرية',
                    'severity': 'medium',
                    'clause': 'معايير التأهيل',
                    'legal_ref': 'المبدأ العام لحرية الوصول إلى الطلب العمومي'
                })

        # تحديد الحالة
        if score >= 85:
            status = 'compliant'
            recommendations = "دفتر الشروط يفي بالمعايير الوطنية للمنافسة والشفافية."
        elif score >= 65:
            status = 'warning'
            recommendations = "يُوصى بإرسال مذكرة توجيهية للمصلحة المتعاقدة لتعديل البنود المقيدة للمنافسة قبل نشر الإعلان النهائي."
        else:
            status = 'violating'
            recommendations = "شبهة تفصيل مواصفات موجهة لصالح متعامل محدد. يُوصى بتجميد الصفقة وطلب إعادة صياغة دفتر الشروط."

        report, _ = RFPAuditReport.objects.update_or_create(
            tender=tender,
            defaults={
                'compliance_status': status,
                'compliance_score': max(0, score),
                'tailored_specs_detected': tailored_specs,
                'findings': findings,
                'recommendations': recommendations,
            }
        )
        return report
