from decimal import Decimal
from apps.ai_authority.models import GeneratedRFP


class RFPDraftingEngine:
    """
    محرك توليد وصياغة مسودات دفاتر الشروط المتوافقة مع المرسوم الرئاسي 23-12
    """

    @classmethod
    def generate_rfp(cls, authority_user, project_title: str, sector: str, procedure_type: str, budget: float = None, duration: int = 6) -> GeneratedRFP:
        # سلم التنقيط التقني حسب القطاع
        if sector == 'works':
            scoring_criteria = {
                'experience_and_references': {'points': 30, 'title': 'الخبرة والمراجع المهنية في مشاريع مماثلة'},
                'technical_equipment': {'points': 25, 'title': 'العتاد والآليات المخصصة للمشروع ومبررات الملكية'},
                'supervisory_staff': {'points': 25, 'title': 'كفاءة وتأهيل الطاقم البشري والتأطير التقني'},
                'execution_methodology': {'points': 20, 'title': 'منهجية الإنجاز والمخطط الزمني للورشة'},
            }
            admin_cond = "يجب على المتعهد تقديم شهادة التأهيل والتصنيف المهنيين في مجال البناء والأشغال العمومية والري سارية المفعول (الدرجة الثالثة فما فوق)، بالإضافة إلى مستخرجات الضرائب والضمان الاجتماعي (CASNOS / CNAS)."
            tech_specs = f"يشمل المشروع إنجاز كافة الأشغال وفق المعايير التقنية المعمول بها لمشروع: {project_title}. مع الالتزام بالمخططات الهندسية ومطابقة المواد المستخدمة للمواصفات القياسية الوطنية، وفترة ضمان تعاقدية قدرها 12 شهراً ابتداءً من الاستلام المؤقت."
        elif sector == 'supplies':
            scoring_criteria = {
                'product_quality_and_specs': {'points': 35, 'title': 'مطابقة المواصفات التقنية وشهادات المنشأ والضمان'},
                'delivery_schedule': {'points': 25, 'title': 'آجال وجداول التسليم والتركيب'},
                'after_sales_service': {'points': 20, 'title': 'خدمات ما بعد البيع وتوفر قطع الغيار محلياً'},
                'similar_references': {'points': 20, 'title': 'مراجع التوريد السابقة لهيئات عمومية'},
            }
            admin_cond = "يجب تقديم السجل التجاري الإلكتروني الذي يتضمن رمز النشاط المطابق لموضوع التوريد، مع بطاقة التعريف الجبائي (NIF) وشهادة عدم الإفلاس أو التسوية القضائية."
            tech_specs = f"توريد وتركيب وتشغيل التجهيزات والمعدات الخاصة بـ: {project_title}، جديدة وغير مستعملة مع ضمان صانع لا يقل عن 24 شهراً وتقديم شهادة مطابقة وكتالوجات تقنية معتمدة أو ما يعادلها."
        elif sector == 'studies':
            scoring_criteria = {
                'expert_team_qualifications': {'points': 40, 'title': 'المؤهلات العلمية وسير ذاتية للخبراء والمهندسين'},
                'methodological_approach': {'points': 30, 'title': 'المقاربة المنهجية وخطة تنفيذ الدراسة'},
                'similar_study_references': {'points': 20, 'title': 'الدراسات والمخططات المنجزة سابقاً في نفس التخصص'},
                'study_timeline': {'points': 10, 'title': 'البرنامج الزمني لتقديم مراحل الدراسة والتقارير'},
            }
            admin_cond = "يشترط التسجيل في الجدول الوطني للمهندسين المعماريين أو نقابة المهندسين المعتمدين، مع اعتماد المكاتب الاستشارية المؤهلة قانوناً."
            tech_specs = f"إعداد الدراسات التقنية والتفصيلية، المخططات التنفيذية، وإعداد دفاتر الشروط للمرحلة اللاحقة الخاصة بـ: {project_title} مع تسليم كافة التقارير بنسخ ورقية ورقمية قابلة للتعديل."
        else: # services
            scoring_criteria = {
                'service_methodology': {'points': 30, 'title': 'مخطط التدخل وجودة تنظيم الخدمات'},
                'staff_qualification': {'points': 30, 'title': 'تأهيل وتدريب الفرق العاملة'},
                'similar_service_contracts': {'points': 25, 'title': 'عقود خدمات مماثلة خلال السنوات الثلاث الأخيرة'},
                'response_time': {'points': 15, 'title': 'سرعة الاستجابة وجاهزية فرق الدعم والصيانة'},
            }
            admin_cond = "تقديم الاعتمادات والتراخيص القانونية لممارسة النشاط وشهادات تسوية الوضعية الجبائية وشبه الجبائية."
            tech_specs = f"تقديم خدمات شاملة ومتواصلة لموضوع: {project_title} مع توفير نظام تقارير دورية وإشراف مستمر على جودة الأداء."

        required_documents = [
            'رسالة الترشح والتصريح بالنزاهة وفق النموذج الرسمي',
            'التصريح بالاكتتاب وتصريح المترشح',
            'القانون الأساسي للشركة والسجل التجاري الإلكتروني',
            'شهادة التأهيل والتصنيف أو الاعتماد المهني',
            'المراجع المهنية والشهادات المماثلة المسلمة من المصالح المتعاقدة',
            'العرض المالي: رسالة التعهد، جدول الأسعار الأحادية (BPU)، والتفصيل الكمي والتقديري (DQE)'
        ]

        rfp = GeneratedRFP.objects.create(
            authority=authority_user,
            project_title=project_title,
            sector=sector,
            procedure_type=procedure_type,
            estimated_budget=budget,
            execution_duration_months=duration,
            administrative_conditions=admin_cond,
            technical_specs=tech_specs,
            scoring_criteria=scoring_criteria,
            required_documents=required_documents,
        )
        return rfp
