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
        
    # Simulate AI processing delay (2 seconds)
    time.sleep(2)
    
    # Mock AI Evaluation Logic
    evaluations = []
    best_bid = None
    best_score = -1
    
    for bid in bids:
        # Calculate a pseudo-score (1 to 100)
        # Lower financial offer is better (assuming tender.budget is the max)
        financial_score = 0
        if tender.budget and bid.financial_offer <= tender.budget:
            financial_score = int(((tender.budget - bid.financial_offer) / tender.budget) * 40) + 10
        elif tender.budget and bid.financial_offer > tender.budget:
            financial_score = 5 # Penalty for going over budget
            
        # Delivery time (lower is better, max 20 points)
        time_score = 20 - (bid.delivery_time_days or 30) // 10
        time_score = max(5, min(20, time_score))
        
        # Warranty (higher is better, max 20 points)
        warranty_score = min(20, (bid.warranty_months or 12))
        
        # Experience (higher is better, max 20 points)
        exp_score = min(20, (bid.similar_projects_count or 0) * 2)
        
        total_score = financial_score + time_score + warranty_score + exp_score
        
        # Some randomness to make it look "AI" fuzzy
        total_score += random.randint(-5, 5)
        total_score = max(10, min(99, total_score))
        
        if total_score > best_score:
            best_score = total_score
            best_bid = bid
            
        # Generate insight text
        strengths = []
        weaknesses = []
        
        if financial_score > 30: strengths.append("عرض مالي ممتاز وتنافسي.")
        else: weaknesses.append("العرض المالي مرتفع نسبياً.")
            
        if bid.delivery_time_days and bid.delivery_time_days < 60: strengths.append("مدة إنجاز سريعة.")
        if bid.warranty_months and bid.warranty_months >= 24: strengths.append("فترة ضمان ممتازة.")
        if bid.similar_projects_count and bid.similar_projects_count >= 5: strengths.append("خبرة قوية ومشاريع مماثلة متعددة.")
        else: weaknesses.append("نقص في الخبرة الموثقة في مشاريع مماثلة.")
            
        evaluations.append({
            'bid_id': bid.id,
            'supplier_name': bid.supplier_name,
            'score': total_score,
            'financial_offer': float(bid.financial_offer),
            'strengths': strengths,
            'weaknesses': weaknesses,
            'summary': f"حصل هذا العرض على تقييم {total_score}/100. يعتبر خياراً {'جيداً' if total_score > 70 else 'متوسطاً'} بناءً على المعايير التقنية والمالية."
        })
        
    # Sort evaluations by score descending
    evaluations.sort(key=lambda x: x['score'], reverse=True)
    
    ai_recommendation = ""
    if best_bid:
        ai_recommendation = f"بناءً على التحليل الشامل للعروض التقنية والمالية، يوصي الذكاء الاصطناعي باختيار عرض **{best_bid.supplier_name}** الذي حصل على أعلى تقييم ({best_score}/100) نظرًا لتوازنه المثالي بين التكلفة، الآجال، والخبرة التقنية."
        
    return JsonResponse({
        'success': True,
        'tender_title': tender.title,
        'evaluations': evaluations,
        'recommendation': ai_recommendation
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
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
        
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({'error': 'Empty message'}, status=400)
            
        # Simulate AI processing
        time.sleep(1)
        
        # Simple rule-based mock for Chatbot
        response = "عذراً، لم أفهم سؤالك بوضوح. هل يمكنك إعادة صياغته؟"
        
        if "قانون" in message or "23-12" in message:
            response = "القانون 23-12 يحدد القواعد العامة للصفقات العمومية في الجزائر، ويركز على الشفافية، الرقمنة، وتكافؤ الفرص بين المتعاملين."
        elif "دفتر الشروط" in message:
            response = "يمكنك سحب دفتر الشروط من صفحة تفاصيل الصفقة. إذا كانت هناك رسوم، يجب دفعها أولاً عبر المنصة لتتمكن من التحميل."
        elif "عروض" in message or "تقييم" in message:
            response = "يتم تقييم العروض باستخدام تقنيات الذكاء الاصطناعي التي تحلل العرض المالي والتقني لتقديم توصية شفافة للمصلحة المتعاقدة."
        elif "مرحبا" in message or "السلام" in message:
            response = f"مرحباً بك {request.user.full_name} في منصة صفقات ذكية! كيف يمكنني مساعدتك اليوم؟"
            
        return JsonResponse({
            'success': True,
            'response': response
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def generate_smart_bid_view(request, tender_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
        
    try:
        tender = Tender.objects.get(id=tender_id)
        
        # Simulate AI generation time
        time.sleep(2)
        
        # Smart Logic for AI Proposal
        budget = float(tender.budget) if tender.budget else 5000000.0
        
        # Calculate a highly competitive financial offer (between 2% to 8% less than budget)
        discount_percentage = random.uniform(0.02, 0.08)
        proposed_offer = budget - (budget * discount_percentage)
        proposed_offer = round(proposed_offer, 2)
        
        # Calculate logical metrics based on budget size
        if budget > 10000000:
            team_size = random.randint(15, 30)
            delivery = random.randint(90, 180)
            warranty = 24
            exp_count = random.randint(8, 15)
        else:
            team_size = random.randint(5, 12)
            delivery = random.randint(30, 60)
            warranty = 12
            exp_count = random.randint(3, 7)
            
        # Draft a technical proposal text
        company_name = request.user.company_name or request.user.full_name
        
        technical_text = (
            f"بصفتنا شركة {company_name}، وبعد دراسة متأنية لدفتر الشروط الخاص بمشروع ({tender.title})، "
            f"يسعدنا تقديم هذا العرض التقني والمالي المتكامل.\n\n"
            f"**المنهجية وخطة العمل:**\n"
            f"1. **المرحلة التحضيرية:** تخصيص فريق يتكون من {team_size} خبراء وتقنيين لبدء العمل الفوري لضمان احترام آجال التسليم المحددة بـ {delivery} يوماً.\n"
            f"2. **مرحلة التنفيذ:** استخدام أحدث التقنيات لضمان جودة تتوافق تماماً مع المعايير المطلوبة في دفتر الشروط.\n"
            f"3. **ضمان الجودة:** نلتزم بتقديم فترة ضمان شاملة لمدة {warranty} شهراً مع صيانة دورية مجانية.\n\n"
            f"نضع تحت تصرفكم خبرتنا الممتدة في إنجاز {exp_count} مشاريع مماثلة بنجاح تام، ونضمن لكم تقديم أفضل جودة بسعر تنافسي جداً وهو {proposed_offer:,.2f} دج، وهو عرض تم دراسته ليكون الأفضل تقنياً ومالياً."
        )
        
        return JsonResponse({
            'success': True,
            'financial_offer': proposed_offer,
            'technical_team_size': team_size,
            'delivery_time_days': delivery,
            'warranty_months': warranty,
            'similar_projects_count': exp_count,
            'technical_notes': technical_text
        })
        
    except Tender.DoesNotExist:
        return JsonResponse({'error': 'الصفقة غير موجودة'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

