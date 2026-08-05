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
        'message': 'جاري تقييم العروض باستخدام الذكاء الاصطناعي في الخلفية. يرجى الانتظار...'
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
            
        # Simulate AI API call delay
        time.sleep(2)
        
        # Mock AI Draft Generation
        draft = f"استناداً لأحكام المرسوم الرئاسي رقم 15-247 المتضمن تنظيم الصفقات العمومية وتفويضات المرفق العام (والمعدل لاحقاً بقانون الصفقات الجديد 23-12)، تعلن المصلحة المتعاقدة عن إطلاق طلب عروض مفتوح لمشروع: {title}.\n\n"
        
        if sector:
            draft += f"**قطاع النشاط:** {sector}\n\n"
            
        draft += "يتضمن هذا المشروع توفير الخدمات/السلع اللازمة وفقاً للمعايير التقنية المحددة في دفتر الشروط المرفق. يُشترط في المتقدمين أن يمتلكوا الخبرة والكفاءة اللازمة لتنفيذ المشروع في الآجال المحددة.\n\n"
        draft += "**المتطلبات الأساسية:**\n"
        draft += "- تقديم العرض المالي والتقني في أظرفة منفصلة ومغلقة.\n"
        draft += "- إرفاق نسخة من السجل التجاري والبطاقة الجبائية.\n"
        draft += "- شهادة حسن التنفيذ لمشاريع سابقة مشابهة (إن وجدت).\n\n"
        draft += "تلتزم المصلحة المتعاقدة بضمان شفافية ونزاهة عملية التقييم، وسيتم منح الصفقة للعرض الذي يقدم أفضل توازن بين التكلفة والجودة بناءً على سلم التقييم."
        
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
        
    # In a real app, this would call the AI API to generate a massive document.
    # Here we mock the AI generation with a structured template.
    
    # Simulate AI processing delay
    time.sleep(2)
    
    context = {
        'tender': tender,
        'generation_date': time.strftime("%Y/%m/%d"),
    }
    
    return render(request, 'ai/cahier_des_charges.html', context)

@login_required
def chatbot_view(request):
    return JsonResponse({
        'success': False,
        'response': 'تم إيقاف ميزة المساعد الذكي مؤقتاً للتركيز على الأساسيات.'
    })

@login_required
def generate_smart_bid_view(request, tender_id):
    return JsonResponse({
        'error': 'تم إيقاف هذه الميزة مؤقتاً. يرجى تحضير عرضك الفعلي ورفعه.'
    }, status=403)


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
