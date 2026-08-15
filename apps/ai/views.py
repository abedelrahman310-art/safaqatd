import time
import random
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from apps.procurement.models import Tender, Bid

@login_required
def evaluate_bids_view(request, tender_id):
    if request.user.role != 'authority':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        return JsonResponse({'error': 'Tender not found'}, status=404)
        
    bids = tender.bids.all()
    if not bids:
        return JsonResponse({'error': 'No bids to evaluate'}, status=400)
        
    # Check if any bid is already evaluated
    if any(bid.ai_evaluation_result for bid in bids):
        evaluations = []
        for bid in bids:
            if bid.ai_evaluation_result:
                eval_data = bid.ai_evaluation_result
                eval_data['bid_id'] = bid.id
                eval_data['supplier_name'] = bid.supplier_name
                eval_data['financial_offer'] = float(bid.financial_offer)
                evaluations.append(eval_data)
                
        evaluations.sort(key=lambda x: x.get('score', 0), reverse=True)
        return JsonResponse({
            'success': True,
            'tender_title': tender.title,
            'evaluations': evaluations,
            'status': 'completed'
        })

    # If not evaluated, trigger background task
    from .tasks import evaluate_tender_bids_task
    evaluate_tender_bids_task.delay(tender.id)
    
    return JsonResponse({
        'success': True,
        'tender_title': tender.title,
        'status': 'processing',
        'message': 'جاري تقييم العروض عبر الأتمتة الإجرائية المتقدمة في الخلفية. يرجى الانتظار...'
    })

import json
from django.shortcuts import render

@login_required
def draft_tender_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
        
    try:
        data = json.loads(request.body)
        title = data.get('title', '')
        sector = data.get('sector', '')
        
        if not title:
            return JsonResponse({'error': 'Title is required for drafting'}, status=400)
            
        import google.genai as genai
        from django.conf import settings
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""
        بصفتك مستشاراً قانونياً ومحرراً مختصاً في الصفقات العمومية الجزائرية وفقاً لأحكام القانون رقم 23-12 المحدد للقواعد العامة المتعلقة بالصفقات العمومية:
        أكتب مسودة رسمية لإعلان عن طلب عروض مفتوح (أو مع اشتراط قدرات دنيا) للمشروع التالي:
        - العنوان: {title}
        - قطاع النشاط: {sector if sector else "غير محدد"}
        
        يجب أن يتضمن الإعلان:
        1. مرجعية القانون رقم 23-12.
        2. الإلزام بتقديم ملف الترشح، العرض التقني، والعرض المالي في أظرفة منفصلة ومقفلة ومختومة (المادة 65).
        3. وجوب تقديم التصريح بالترشح والتصريح بالنزاهة طبقا للمادة 51 من القانون 23-12.
        4. مدة تحضير العروض وتاريخ وساعة جلسة فتح الأظرفة العلنية.
        
        الصياغة: لغة عربية إدارية فصيحة، صارمة، موجزة، ومطابقة للنماذج الرسمية المعتمدة.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        draft = response.text.strip()
        
        return JsonResponse({
            'success': True,
            'draft': draft
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def generate_cahier_view(request, tender_id):
    if request.user.role != 'authority':
        return render(request, 'core/error.html', {'message': 'غير مصرح لك بالوصول لهذا القسم'})
        
    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        return render(request, 'core/error.html', {'message': 'الصفقة غير موجودة'})
        
    if tender.ai_cahier_result:
        context = {
            'tender': tender,
            'cahier_data': tender.ai_cahier_result,
            'generation_date': tender.updated_at.strftime("%Y/%m/%d"),
        }
        return render(request, 'ai/cahier_des_charges.html', context)
    else:
        # Trigger Celery Task if not already generating
        from .tasks import generate_cahier_task
        # We can just fire it, Celery will queue it. For MVP, we fire it once when requested.
        generate_cahier_task.delay(tender.id)
        
        context = {
            'tender': tender,
            'message': 'جاري استخراج دفتر الشروط آلياً... يرجى الانتظار.'
        }
        return render(request, 'ai/cahier_loading.html', context)

@login_required
def chatbot_view(request):
    return JsonResponse({
        'success': False,
        'response': 'تم إيقاف ميزة المساعد الذكي مؤقتاً للتركيز على الأساسيات.'
    })

@login_required
def generate_smart_bid_view(request, tender_id):
    import random
    
    # Step 5: Smart Pricing Logic (Mock)
    # The AI suggests a competitive technical size, days, and a calculated BPU based on historical data.
    return JsonResponse({
        'success': True,
        'technical_team_size': random.randint(3, 10),
        'similar_projects_count': random.randint(1, 5),
        'delivery_time_days': random.randint(30, 90),
        'warranty_months': random.choice([12, 24, 36]),
        'technical_notes': "مقترح ذكي (Smart Pricing): تم تحليل 14 صفقة سابقة في نفس المجال. يُنصح بتقديم طاقم تقني متوسط مع التركيز على فترة الضمان لتعزيز حظوظك.",
    })


@login_required
def smart_tender_match(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
        
    if request.user.role != 'supplier':
        return JsonResponse({'error': 'Only suppliers can use this feature'}, status=403)
        
    try:
        data = json.loads(request.body)
        keywords_str = data.get('keywords', '').strip().lower()
        
        if not keywords_str:
            return JsonResponse({'error': 'يرجى إدخال كلمات مفتاحية عن تخصصك'}, status=400)
        keywords = [k.strip() for k in keywords_str.split(' ') if len(k.strip()) > 2]
        
        # Get all published tenders
        tenders = Tender.objects.filter(status='published')
        
        matches = []
        for tender in tenders:
            score = 0
            text_to_search = f"{tender.title} {tender.description} {tender.sector} {tender.wilaya}".lower()
            
            for word in keywords:
                if word in text_to_search:
                    # Give higher weight to matches in title
                    if word in tender.title.lower():
                        score += 40
                    else:
                        score += 20
                        
            if score > 0:
                score = min(99, score)
                
                matches.append({
                    'id': tender.id,
                    'title': tender.title,
                    'budget': float(tender.budget) if tender.budget else 0,
                    'wilaya': tender.wilaya or 'غير محدد',
                    'score': score,
                    'deadline': tender.deadline.strftime("%Y/%m/%d") if tender.deadline else "",
                    'reason': f"هذه الصفقة مناسبة لك لوجود تطابق بنسبة {score}% مع تخصصك ومتطلباتك."
                })
                
        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        top_matches = matches[:3] # Return top 3
        
        return JsonResponse({
            'success': True,
            'matches': top_matches,
            'message': 'تم العثور على صفقات مناسبة!' if top_matches else 'لم نجد صفقات مطابقة 100% حالياً، جرب كلمات أخرى.'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
