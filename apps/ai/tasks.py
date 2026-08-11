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
                أنت خبير في تقييم العروض للصفقات العمومية الجزائرية.
                ميزانية المشروع التقديرية: {tender.budget}
                قم بتحليل هذا النص المستخرج من العرض المالي للمقاول {bid.supplier_name} وأعطني تقييماً من 100، 
                مع استخراج نقاط القوة والضعف بشكل مهيكل في صيغة JSON تحتوي على:
                - score (من 100)
                - strengths (قائمة نصوص)
                - weaknesses (قائمة نصوص)
                - summary (نص ملخص)
                
                نص العرض المالي:
                {financial_text[:2000]}  # limit text length for MVP
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
        أنت خبير قانوني وتقني في إعداد دفاتر الشروط (Cahier des charges) للصفقات العمومية الجزائرية.
        قم بإنشاء دفتر شروط مفصل للمشروع التالي:
        - العنوان: {tender.title}
        - الوصف: {tender.description}
        - الميزانية التقديرية: {tender.budget} دج
        - قطاع النشاط: {tender.sector}
        - الولاية: {tender.wilaya}
        - نوع الصفقة: {tender.get_tender_type_display()}
        
        قم بإرجاع النتيجة حصراً بصيغة JSON مهيكلة تحتوي على الحقول التالية:
        {{
            "title": "عنوان دفتر الشروط",
            "legal_framework": "الإطار القانوني والتنظيمي (نص طويل)",
            "technical_requirements": "المتطلبات التقنية والمواصفات (نص طويل)",
            "evaluation_criteria": "شروط التقييم والتأهيل (نص طويل)"
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
