from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.procurement.models import Tender
from apps.ai_regulator.models import CollusionAlert, RFPAuditReport, TenderRiskScore
from apps.ai_regulator.services.collusion_detector import CollusionDetectionEngine
from apps.ai_regulator.services.rfp_auditor import RFPAuditorEngine
from apps.ai_regulator.services.legal_advisor import LegalAdvisorEngine


@login_required
def radar_dashboard_view(request):
    """
    شاشة رادار الرقابة الذكية وكشف شبهات التواطؤ ومؤشرات الخطر
    """
    # فحص تلقائي لتحديث الإنذارات
    tenders = Tender.objects.all()
    for tender in tenders[:10]:
        CollusionDetectionEngine.scan_tender(tender)
        if not hasattr(tender, 'rfp_audit'):
            RFPAuditorEngine.audit_tender(tender)

    alerts = CollusionAlert.objects.select_related('tender').prefetch_related('involved_suppliers').all()
    rfp_reports = RFPAuditReport.objects.select_related('tender').all()

    # إحصائيات سريعة
    critical_alerts_count = alerts.filter(severity='high').count()
    medium_alerts_count = alerts.filter(severity='medium').count()
    violating_rfp_count = rfp_reports.filter(compliance_status='violating').count()

    context = {
        'alerts': alerts,
        'rfp_reports': rfp_reports,
        'critical_alerts_count': critical_alerts_count,
        'medium_alerts_count': medium_alerts_count,
        'violating_rfp_count': violating_rfp_count,
        'total_alerts_count': alerts.count(),
    }
    return render(request, 'ai_regulator/radar_dashboard.html', context)


@login_required
def rfp_auditor_view(request, tender_id=None):
    """
    واجهة الفاحص الذكي لدفاتر الشروط
    """
    selected_tender = None
    audit_report = None

    if tender_id:
        selected_tender = get_object_or_404(Tender, id=tender_id)
        audit_report = RFPAuditorEngine.audit_tender(selected_tender)

    tenders = Tender.objects.all().order_by('-created_at')

    context = {
        'tenders': tenders,
        'selected_tender': selected_tender,
        'audit_report': audit_report,
    }
    return render(request, 'ai_regulator/rfp_auditor.html', context)


@login_required
def legal_copilot_view(request):
    """
    المساعد الاستشاري القانوني السيادي
    """
    query_text = request.GET.get('q', '').strip()
    result = None
    if query_text:
        result = LegalAdvisorEngine.query(query_text)

    context = {
        'query_text': query_text,
        'result': result,
    }
    return render(request, 'ai_regulator/legal_copilot.html', context)
