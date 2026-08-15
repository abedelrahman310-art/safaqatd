import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
from apps.procurement.models import Tender, Bid

from .services.regulator_stats import get_regulator_summary, get_visible_tenders, apply_regulator_filters
from .services.regulator_reports import RegulatorReportsService
from .forms import RegulatorFilterForm
from .filters import TenderFilter
from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin

class RegulatorDashboardView(PermissionRequiredMixin, TemplateView):
    template_name = 'dashboard/regulator_dashboard.html'
    permission_required = "accounts.view_central_dashboard"

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        context = super().get_context_data(**kwargs)
        request = self.request
        
        filter_form = RegulatorFilterForm(request.GET or None)
        
        filters = {}
        if filter_form.is_valid():
            filters = filter_form.cleaned_data
            
        summary = get_regulator_summary(request.user, filters)
        context.update(summary)
        
        # Paginate tenders
        paginator = Paginator(summary['tenders'], 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        
        context['filter'] = type('obj', (object,), {'form': filter_form}) # Mocking the TenderFilter interface for the template `filter.form`
        
        request.session['regulator_dashboard_filters'] = request.GET.dict()
        
        # Mock Data for Integrity Radar (Red/Orange Flags)
        context['integrity_alarms'] = [
            {'tender_id': 105, 'title': 'بناء مجمع إداري - وهران', 'severity': 'red', 'reason': 'تطابق أسعار غير اعتيادي (احتمال تواطؤ)', 'date': '2026-08-12'},
            {'tender_id': 204, 'title': 'تجهيز معدات طبية - العاصمة', 'severity': 'orange', 'reason': 'فوز متكرر لنفس الشركة (احتكار محتمل)', 'date': '2026-08-10'},
            {'tender_id': 301, 'title': 'تهيئة شبكة الطرق - ورقلة', 'severity': 'orange', 'reason': 'انسحاب مفاجئ لثلاثة موردين', 'date': '2026-08-09'},
        ]
        
        # Mock Predictive Analytics Data
        context['predictive_labels'] = ['أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر', 'يناير']
        context['predictive_prices'] = [100, 105, 112, 120, 125, 135] # Example: Construction materials index
        context['predictive_tenders'] = [50, 45, 42, 38, 30, 25] # Example: Expected volume
        
        # Update context total with Transparency Rate & Growth Index
        context['transparency_rate'] = "94%"
        context['growth_index'] = "+12%"
        
        return context

import csv
import logging
from django.http import StreamingHttpResponse

logger = logging.getLogger('dashboard.exports')

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        return value

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def export_regulator_csv(request):
    logger.info(f"User {request.user} exported CSV. Filters: {request.session.get('regulator_dashboard_filters', {})}")
    filters = request.session.get('regulator_dashboard_filters', {})
    qs = get_visible_tenders(request.user)
    queryset = apply_regulator_filters(qs, filters)
    
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    def generate():
        # BOM for UTF-8 Excel compatibility
        yield pseudo_buffer.write('\ufeff')
        yield writer.writerow([
            "رقم الصفقة",
            "العنوان",
            "الحالة",
            "التاريخ",
        ])
        for tender in queryset.iterator(chunk_size=500):
            yield writer.writerow([
                tender.id,
                tender.title,
                tender.get_status_display(),
                tender.created_at.strftime('%Y-%m-%d %H:%M') if tender.created_at else '',
            ])

    response = StreamingHttpResponse(
        generate(),
        content_type="text/csv; charset=utf-8"
    )
    response["Content-Disposition"] = 'attachment; filename="tenders_report.csv"'
    return response

from django.http import JsonResponse

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def freeze_tender_view(request, tender_id):
    if request.method == "POST":
        tender = get_object_or_404(Tender, id=tender_id)
        tender.is_frozen = not tender.is_frozen
        tender.save()
        status = "تجميد" if tender.is_frozen else "إلغاء التجميد"
        messages.success(request, f"تم {status} الصفقة #{tender.id} بنجاح.")
        return redirect('dashboard:regulator')
    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def fetch_blockchain_ledger_view(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    # Mock blockchain ledger data
    ledger_entries = [
        {"timestamp": "2026-08-10T10:00:00Z", "action": "Tender Published", "hash": "0x8F9B2A...4D3C", "actor": "Authority"},
        {"timestamp": "2026-08-11T14:30:00Z", "action": "Bid Submitted (Encrypted)", "hash": "0x1A2B3C...9D8E", "actor": "Supplier A"},
        {"timestamp": "2026-08-12T09:15:00Z", "action": "Bid Submitted (Encrypted)", "hash": "0x5E6F7G...1H2I", "actor": "Supplier B"}
    ]
    return JsonResponse({"tender_id": tender.id, "ledger": ledger_entries})

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def export_regulator_pdf(request):
    logger.info(f"User {request.user} exported PDF. Filters: {request.session.get('regulator_dashboard_filters', {})}")
    filters = request.session.get('regulator_dashboard_filters', {})
    qs = get_visible_tenders(request.user)
    filtered_qs = apply_regulator_filters(qs, filters)
    return RegulatorReportsService.generate_pdf_report(filtered_qs)

@login_required
@permission_required('accounts.manage_all_users', raise_exception=True)
def regulator_users_list(request):
    User = get_user_model()
    # Base queryset excluding superusers and current user
    base_qs = User.objects.exclude(is_superuser=True).exclude(id=request.user.id).order_by('-date_joined')
    
    # Separate users by role
    authorities = base_qs.filter(role='authority')
    suppliers = base_qs.filter(role='supplier')
    admins = base_qs.filter(role='central_admin')

    context = {
        'authorities': authorities,
        'suppliers': suppliers,
        'admins': admins,
        'count_all': base_qs.count(),
        'count_authorities': authorities.count(),
        'count_suppliers': suppliers.count(),
        'count_admins': admins.count(),
        'active_tab': request.GET.get('tab', 'authorities'),
    }
    return render(request, 'dashboard/regulator_users.html', context)

@login_required
@permission_required('accounts.manage_all_users', raise_exception=True)
def toggle_user_status(request, user_id):
    if request.method == 'POST':
        User = get_user_model()
        target_user = get_object_or_404(User, id=user_id)
        
        # Prevent banning superusers or oneself
        if target_user.is_superuser or target_user == request.user:
            messages.error(request, 'لا يمكن تعديل حالة هذا المستخدم.')
        else:
            target_user.is_active = not target_user.is_active
            target_user.save()
            status_msg = "تم تفعيل" if target_user.is_active else "تم حظر"
            messages.success(request, f'{status_msg} حساب {target_user.get_full_name() or target_user.username} بنجاح.')
            
    return redirect('dashboard:regulator_users')

@login_required
@permission_required('accounts.audit_all_tenders', raise_exception=True)
def regulator_audit_list(request):
    tenders = Tender.objects.select_related('authority').prefetch_related('bids').order_by('-created_at')
    
    context = {
        'tenders': tenders,
    }
    return render(request, 'dashboard/regulator_audit.html', context)

@login_required
@permission_required('accounts.audit_all_tenders', raise_exception=True)
def regulator_audit_detail(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    history = tender.history.all().order_by('-history_date')
    bids = tender.bids.all().order_by('-submitted_at')
    
    # Calculate simple stats
    bids_count = bids.count()
    
    # Detect red flags (e.g., changes after published, low bids)
    red_flags = []
    if bids_count > 0 and bids_count < 3 and tender.status == 'closed':
        red_flags.append('عدد العروض أقل من 3، يجب مراجعة مبدأ المنافسة.')
        
    for h in history:
        if h.status == 'published' and h.history_type == '~':
            # Example heuristic: If it was modified while published
            pass
            
    context = {
        'tender': tender,
        'history': history,
        'bids': bids,
        'red_flags': red_flags,
    }
    return render(request, 'dashboard/regulator_audit_detail.html', context)

from apps.procurement.models import Tender, Bid, AnnualBudget, PlannedProject
from django.db.models import Sum
from django.utils import timezone

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def planning_department_view(request):
    current_year = timezone.now().year
    
    # Get all budgets for the current year
    budgets = AnnualBudget.objects.filter(year=current_year)
    total_budget = budgets.aggregate(Sum('total_budget'))['total_budget__sum'] or 0
    
    # Get all planned projects
    planned_projects = PlannedProject.objects.filter(budget__year=current_year)
    planned_value = planned_projects.aggregate(Sum('estimated_value'))['estimated_value__sum'] or 0
    
    # Calculate consumed amount (from actual tenders linked to planned projects)
    consumed_projects = planned_projects.filter(is_launched=True)
    consumed_value = consumed_projects.aggregate(Sum('tender__budget'))['tender__budget__sum'] or 0
    
    context = {
        'current_year': current_year,
        'total_budget': total_budget,
        'planned_value': planned_value,
        'consumed_value': consumed_value,
        'budgets': budgets,
        'planned_projects': planned_projects.order_by('-created_at')[:10], # recent 10
    }
    return render(request, 'dashboard/planning_department.html', context)


import sys
import platform
from django.db import connection
from django.core.cache import cache

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def system_health_view(request):
    from django.shortcuts import redirect
    return redirect('system_health:dashboard')

# --- Central Admin / Regulator Fully Activated Views ---
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from apps.procurement.models import ProcurementAuditLog

@login_required
@permission_required('accounts.manage_all_users')
def regulator_authorities_view(request):
    User = get_user_model()
    q = request.GET.get('q', '').strip()
    sector = request.GET.get('sector', '').strip()
    
    authorities = User.objects.filter(role='authority').annotate(
        tenders_count=Count('tenders', distinct=True),
        total_budget_sum=Sum('tenders__budget')
    ).order_by('-date_joined')
    
    if q:
        authorities = authorities.filter(
            Q(username__icontains=q) | 
            Q(email__icontains=q) | 
            Q(full_name__icontains=q) | 
            Q(institution_name__icontains=q) |
            Q(tax_id__icontains=q)
        )
    if sector:
        authorities = authorities.filter(sector=sector)
        
    paginator = Paginator(authorities, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    total_count = User.objects.filter(role='authority').count()
    active_count = User.objects.filter(role='authority', is_active=True).count()
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'sector': sector,
        'total_authorities_count': total_count,
        'active_authorities_count': active_count,
    }
    return render(request, 'dashboard/regulator_authorities.html', context)

@login_required
@permission_required('accounts.manage_all_users')
def regulator_suppliers_view(request):
    User = get_user_model()
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    suppliers = User.objects.filter(role='supplier').annotate(
        bids_count=Count('submitted_bids', distinct=True)
    ).order_by('-date_joined')
    
    if q:
        suppliers = suppliers.filter(
            Q(username__icontains=q) | 
            Q(email__icontains=q) | 
            Q(full_name__icontains=q) | 
            Q(commercial_register__icontains=q) |
            Q(national_id__icontains=q)
        )
    if status_filter == 'blacklisted':
        suppliers = suppliers.filter(is_blacklisted=True)
    elif status_filter == 'active':
        suppliers = suppliers.filter(is_active=True, is_blacklisted=False)
    elif status_filter == 'inactive':
        suppliers = suppliers.filter(is_active=False)
        
    paginator = Paginator(suppliers, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    total_count = User.objects.filter(role='supplier').count()
    blacklisted_count = User.objects.filter(role='supplier', is_blacklisted=True).count()
    active_count = User.objects.filter(role='supplier', is_active=True, is_blacklisted=False).count()
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'status_filter': status_filter,
        'total_suppliers_count': total_count,
        'blacklisted_count': blacklisted_count,
        'active_suppliers_count': active_count,
    }
    return render(request, 'dashboard/regulator_suppliers.html', context)

@login_required
@permission_required('accounts.audit_all_tenders')
def regulator_tenders_view(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    
    tenders = Tender.objects.select_related('authority').prefetch_related('bids').order_by('-created_at')
    
    if q:
        tenders = tenders.filter(
            Q(title__icontains=q) | 
            Q(description__icontains=q) | 
            Q(reference_number__icontains=q) |
            Q(authority__institution_name__icontains=q)
        )
    if status:
        tenders = tenders.filter(status=status)
        
    total_count = Tender.objects.count()
    frozen_count = Tender.objects.filter(is_frozen=True).count()
    active_count = Tender.objects.filter(status='published').count()
    evaluating_count = Tender.objects.filter(status='evaluating').count()
    
    paginator = Paginator(tenders, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'total_tenders_count': total_count,
        'frozen_count': frozen_count,
        'active_count': active_count,
        'evaluating_count': evaluating_count,
    }
    return render(request, 'dashboard/regulator_tenders.html', context)

@login_required
@permission_required('accounts.audit_all_tenders')
def regulator_audit_log_view(request):
    q = request.GET.get('q', '').strip()
    action_type = request.GET.get('action', '').strip()
    
    procurement_logs = ProcurementAuditLog.objects.select_related('actor').order_by('-timestamp')
    if q:
        procurement_logs = procurement_logs.filter(
            Q(action__icontains=q) | 
            Q(actor_role__icontains=q) | 
            Q(entity_type__icontains=q) |
            Q(actor__username__icontains=q)
        )
    if action_type:
        procurement_logs = procurement_logs.filter(action__icontains=action_type)
        
    paginator = Paginator(procurement_logs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Access security logs from axes
    security_logs = []
    try:
        from axes.models import AccessLog
        security_logs = AccessLog.objects.order_by('-attempt_time')[:15]
    except Exception:
        pass
        
    context = {
        'page_obj': page_obj,
        'q': q,
        'action_type': action_type,
        'security_logs': security_logs,
        'total_audit_records': ProcurementAuditLog.objects.count(),
    }
    return render(request, 'dashboard/regulator_audit_log.html', context)

@login_required
@permission_required('accounts.view_central_dashboard')
def regulator_documents_view(request):
    documents = [
        {
            'id': 'REG-2026-01',
            'title': 'المرسوم الرئاسي رقم 23-12 المحدد لقواعد الصفقات العمومية',
            'category': 'تشريعات وقوانين',
            'date': '2026-01-15',
            'size': '2.4 MB',
            'status': 'نافذ وساري',
            'badge_color': '#059669',
        },
        {
            'id': 'SPEC-2026-04',
            'title': 'دفتر الشروط النموذجي للصفقات العمومية للأشغال العامة',
            'category': 'نماذج معيارية',
            'date': '2026-02-01',
            'size': '1.8 MB',
            'status': 'نموذج معتمد',
            'badge_color': '#0284c7',
        },
        {
            'id': 'CIRC-2026-08',
            'title': 'تعليمة وزارية حول آليات فتح الأظرفة الإلكترونية والتشفير',
            'category': 'تعليمات وزارية',
            'date': '2026-03-10',
            'size': '950 KB',
            'status': 'إلزامي للجان',
            'badge_color': '#d97706',
        },
        {
            'id': 'FORM-2026-11',
            'title': 'استمارة التصريح بالنزاهة ومكافحة تضارب المصالح',
            'category': 'وثائق النزاهة',
            'date': '2026-04-05',
            'size': '420 KB',
            'status': 'إلزامي للموردين',
            'badge_color': '#7c3aed',
        },
    ]
    return render(request, 'dashboard/regulator_documents.html', {'documents': documents})

@login_required
@permission_required('accounts.view_central_dashboard')
def regulator_notifications_view(request):
    alerts = [
        {
            'title': 'تنبيه نظام النزاهة: رصد تطابق في عنوان IP لشركتين متنافستين',
            'tender': 'مشروع بناء مجمع مدرسي - قسنطينة',
            'time': 'منذ ساعتين',
            'severity': 'high',
            'status': 'قيد التحقيق الرقابي',
        },
        {
            'title': 'إشعار انتهاء أجل تقديم العروض لـ 14 صفقة وطنية',
            'tender': 'قطاع الصحة والأشغال العمومية',
            'time': 'منذ 5 ساعات',
            'severity': 'medium',
            'status': 'جاهزة لفتح الأظرفة',
        },
        {
            'title': 'طلب تجميد صفقة وارد من لجنة تدقيق المصلحة المتعاقدة',
            'tender': 'توريد عتاد إعلام آلي - العاصمة',
            'time': 'منذ يوم',
            'severity': 'high',
            'status': 'تتطلب قراراً مركزياً',
        },
    ]
    return render(request, 'dashboard/regulator_notifications.html', {'alerts': alerts})

@login_required
@permission_required('accounts.view_central_dashboard')
def regulator_support_view(request):
    channels = [
        {'name': 'خلية الدعم الرقابي المركزي', 'desc': 'المساعدة القانونية والطعون الإدارية', 'phone': '023.45.67.89', 'email': 'support.regulator@safaqat.dz'},
        {'name': 'المفتشية العامة للصفقات العمومية', 'desc': 'الإبلاغ عن حالات عدم المطابقة والنزاعات', 'phone': '023.45.67.90', 'email': 'inspection@safaqat.dz'},
        {'name': 'فريق الدعم التقني والتشفير', 'desc': 'أعطال الأختام الرقمية والتوقيع الإلكتروني', 'phone': '023.45.67.91', 'email': 'tech.support@safaqat.dz'},
    ]
    return render(request, 'dashboard/regulator_support.html', {'channels': channels})
