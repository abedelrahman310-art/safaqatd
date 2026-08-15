from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.procurement.models import Tender
from apps.ai_supplier.models import SupplierMatchScore, TenderSummaryAI, BidReadinessReport
from apps.ai_supplier.services.tender_matcher import TenderMatchingEngine
from apps.ai_supplier.services.rfp_summarizer import RFPSummarizerEngine
from apps.ai_supplier.services.bid_compliance_checker import BidPreCheckEngine


@login_required
def tender_recommendations_view(request):
    """
    شاشة الصفقات الموصى بها والمطابقة لنشاط المتعامل الاقتصادي
    """
    matches = TenderMatchingEngine.match_for_supplier(request.user)

    top_matches = [m for m in matches if m.overall_match_score >= 80]

    context = {
        'matches': matches,
        'top_matches_count': len(top_matches),
        'total_opportunities_count': len(matches),
    }
    return render(request, 'ai_supplier/tender_recommendations.html', context)


@login_required
def rfp_quick_summary_view(request, tender_id=None):
    """
    الملخص الذكي لدفتر الشروط والمواصفات للمورد
    """
    selected_tender = None
    summary = None

    if tender_id:
        selected_tender = get_object_or_404(Tender, id=tender_id)
        summary = RFPSummarizerEngine.get_or_generate_summary(selected_tender)

    tenders = Tender.objects.filter(status='published').order_by('-created_at')

    context = {
        'tenders': tenders,
        'selected_tender': selected_tender,
        'summary': summary,
    }
    return render(request, 'ai_supplier/rfp_quick_summary.html', context)


@login_required
def bid_readiness_check_view(request, tender_id=None):
    """
    الفاحص المسبق لاكتمال وثائق العرض وتفادي الإقصاء الإداري
    """
    selected_tender = None
    readiness_report = None

    if tender_id:
        selected_tender = get_object_or_404(Tender, id=tender_id)
        readiness_report = BidPreCheckEngine.analyze_readiness(request.user, selected_tender)

    tenders = Tender.objects.filter(status='published').order_by('-created_at')

    context = {
        'tenders': tenders,
        'selected_tender': selected_tender,
        'readiness_report': readiness_report,
    }
    return render(request, 'ai_supplier/bid_readiness_check.html', context)
