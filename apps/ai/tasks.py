import json
from celery import shared_task
from django.conf import settings
from apps.procurement.models import Tender, Bid
from apps.core.utils import decrypt_file_content

@shared_task
def evaluate_tender_bids_task(tender_id):
    try:
        tender = Tender.objects.get(id=tender_id)
        bids = tender.bids.all()
        
        evaluations = []
        for bid in bids:
            # Note: We must decrypt the file content in memory to read it
            # We are using PyMuPDF (fitz) or just extracting basic text for the MVP
            # Here we simulate real API call logic using google-genai
            import google.genai as genai
            import fitz  # PyMuPDF
            
            try:
                # Initialize Gemini API
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                
                # Decrypt PDF in memory
                if bid.financial_document:
                    decrypted_financial = decrypt_file_content(bid.financial_document.read())
                    doc = fitz.open(stream=decrypted_financial, filetype="pdf")
                    financial_text = ""
                    for page in doc:
                        financial_text += page.get_text()
                else:
                    financial_text = "لا يوجد عرض مالي."
                    
                prompt = f"""
                أنت خبير قانوني ومحاسبي في تدقيق عروض الصفقات العمومية الجزائرية وفق القانون رقم 23-12.
                الميزانية التقديرية للصفقة: {tender.budget} دج
                
                قم بتحليل هذا النص المستخرج من العرض المالي والتقني للمتعامل الاقتصادي {bid.supplier_name}:
                1. فحص الاتساق الحسابي ومطابقة الأسعار المرجعية لمنع العروض المنخفضة بشكل غير طبيعي (Offres anormalement basses) أو العروض المبالغ فيها.
                2. التحقق من الضمانات وسلامة التعهدات المادية والمهنية.
                3. احتساب علامة تقييم من 100 نقطة وفق سلم التنقيط المعتمد.
                
                أرجع النتيجة حصراً بصيغة JSON مهيكلة:
                {{
                    "score": 85,
                    "strengths": ["نقاط القوة في العرض والتوافق القانوني"],
                    "weaknesses": ["التحفظات أو النواقص إن وجدت"],
                    "summary": "ملخص تنفيذي يوجه لجنة التقييم في اتخاذ القرار"
                }}
                
                النص المستخرج:
                {financial_text[:2000]}
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                # Parse JSON from response
                try:
                    result_json = json.loads(response.text.strip('```json\n').strip('```').strip())
                except json.JSONDecodeError:
                    result_json = {
                        "score": 50,
                        "strengths": ["فشل في قراءة مخرجات التقييم الآلي بشكل منظم."],
                        "weaknesses": ["الرجاء إعادة التقييم."],
                        "summary": "خطأ في المعالجة."
                    }
                    
                bid.ai_evaluation_result = result_json
                bid.save()
                evaluations.append(result_json)
                
            except Exception as ai_err:
                # Handle AI failure for specific bid
                bid.ai_evaluation_result = {"error": str(ai_err)}
                bid.save()
                
        return {"status": "success", "evaluated_bids": len(evaluations)}
        
    except Tender.DoesNotExist:
        return {"status": "error", "message": "Tender not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@shared_task
def generate_cahier_task(tender_id):
    try:
        tender = Tender.objects.get(id=tender_id)
        
        import google.genai as genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""
        أنت مستشار قانوني وتنفيذي معتمد في الصفقات العمومية الجزائرية.
        قم بإعداد مسودة متكاملة لدفتر الشروط (Cahier des charges) مطابقة تماماً لأحكام القانون رقم 23-12 المحدد للقواعد العامة المتعلقة بالصفقات العمومية، وللقرارات الوزارية المنظمة.
        
        بيانات الصفقة:
        - العنوان: {tender.title}
        - الموضوع والوصف: {tender.description}
        - الميزانية التقديرية المرجعية: {tender.budget} دج
        - قطاع النشاط: {tender.sector}
        - النطاق الإقليمي (الولاية): {tender.wilaya}
        - الإجراء المعتمد: {tender.get_tender_type_display()}
        
        يجب أن يحترم دفتر الشروط:
        1. شروط المنافسة الحرة ومنع الإشارة إلى ماركات أو علامات محددة إلا بإضافة "أو ما يعادلها".
        2. الإلزام بتقديم الوثائق وفق المادة 51 (التصريح بالترشح، التصريح بالنزاهة، التصريح بالاكتتاب).
        3. تفصيل سلم التنقيط والتقييم على 100 نقطة (العرض التقني + العرض المالي).
        
        قم بإرجاع النتيجة حصراً بصيغة JSON مهيكلة تحتوي على الحقول التالية:
        {{
            "title": "دفتر الشروط النموذجي: {tender.title}",
            "legal_framework": "الإطار القانوني والتنظيمي (تحديد الإحالات القانونية للقانون 23-12 والمواد المنظمة)",
            "technical_requirements": "المتطلبات التقنية، المواصفات الفنية، وآجال الإنجاز والضمانات",
            "evaluation_criteria": "معايير الانتقاء، سلم التنقيط (100 نقطة)، وشروط التأهيل والإقصاء"
        }}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        try:
            result_json = json.loads(response.text.strip('```json\n').strip('```').strip())
        except json.JSONDecodeError:
            result_json = {
                "title": f"دفتر الشروط: {tender.title}",
                "legal_framework": "حدث خطأ في قراءة الرد الآلي.",
                "technical_requirements": "يرجى إعادة المحاولة.",
                "evaluation_criteria": response.text
            }
            
        tender.ai_cahier_result = result_json
        tender.save()
        
        return {"status": "success", "tender_id": tender_id}
        
    except Tender.DoesNotExist:
        return {"status": "error", "message": "Tender not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
