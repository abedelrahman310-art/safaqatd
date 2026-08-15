from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.procurement.models import Tender
from apps.ai_authority.models import GeneratedRFP, AutomatedEvaluationSession, PriceBenchmarkEstimate
from apps.ai_authority.services.rfp_generator import RFPDraftingEngine
from apps.ai_authority.services.bid_evaluator import BidEvaluationEngine
from apps.ai_authority.services.price_estimator import PriceEstimatorEngine


@login_required
def rfp_generator_view(request, rfp_id=None):
    """
    معالج صياغة وتوليد دفاتر الشروط الذكية
    """
    selected_rfp = None
    if rfp_id:
        selected_rfp = get_object_or_404(GeneratedRFP, id=rfp_id, authority=request.user)

    if request.method == 'POST':
        project_title = request.POST.get('project_title', '').strip()
        sector = request.POST.get('sector', 'works')
        procedure_type = request.POST.get('procedure_type', 'open_tender')
        budget = request.POST.get('budget', None)
        duration = int(request.POST.get('duration', 6) or 6)

        budget_val = float(budget) if budget else None

        if project_title:
            new_rfp = RFPDraftingEngine.generate_rfp(
                authority_user=request.user,
                project_title=project_title,
                sector=sector,
                procedure_type=procedure_type,
                budget=budget_val,
                duration=duration
            )
            messages.success(request, 'تم توليد مسودة دفتر الشروط والمعايير التقنية بنجاح!')
            return redirect('ai_authority:rfp_detail', rfp_id=new_rfp.id)

    my_rfps = GeneratedRFP.objects.filter(authority=request.user).order_by('-created_at')

    context = {
        'my_rfps': my_rfps,
        'selected_rfp': selected_rfp,
    }
    return render(request, 'ai_authority/rfp_generator_wizard.html', context)


@login_required
def bid_evaluation_view(request, tender_id=None):
    """
    المساعد الذكي لتقييم العروض وجدول المفاضلة للجنة
    """
    selected_tender = None
    evaluation_session = None

    if tender_id:
        selected_tender = get_object_or_404(Tender, id=tender_id)
        evaluation_session = BidEvaluationEngine.evaluate_tender_bids(selected_tender, request.user)

    # جلب صفقات المصلحة المتعاقدة أو الصفقات المفتوحة
    tenders = Tender.objects.all().order_by('-created_at')

    context = {
        'tenders': tenders,
        'selected_tender': selected_tender,
        'evaluation_session': evaluation_session,
    }
    return render(request, 'ai_authority/bid_evaluation_tool.html', context)


@login_required
def price_estimator_view(request):
    """
    حاسبة الميزانية والأسعار المرجعية العادلة
    """
    estimate_result = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        sector = request.POST.get('sector', 'أشغال')
        approx_size = request.POST.get('approx_size', None)
        size_val = float(approx_size) if approx_size else None

        if title:
            estimate_result = PriceEstimatorEngine.estimate_price(title, sector, size_val)

    recent_estimates = PriceBenchmarkEstimate.objects.all().order_by('-created_at')[:5]

    context = {
        'estimate_result': estimate_result,
        'recent_estimates': recent_estimates,
    }
    return render(request, 'ai_authority/price_estimator.html', context)
