import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model
from django.contrib import messages
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
    # Exclude superusers and the current regulator from the list to prevent accidental self-ban
    users = User.objects.exclude(is_superuser=True).exclude(id=request.user.id).order_by('-date_joined')
    
    return render(request, 'dashboard/regulator_users.html', {'users': users})

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
