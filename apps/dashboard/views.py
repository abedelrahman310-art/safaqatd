from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from apps.procurement.models import Tender, Bid
from apps.accounts.models import User
import json
from django.utils import timezone

@login_required
@permission_required('procurement.view_tender', raise_exception=True)
def authority_dashboard(request):
    my_tenders = Tender.objects.filter(authority=request.user)
    total_tenders = my_tenders.count()
    active_tenders = my_tenders.filter(status='published').count()
    
    my_bids = Bid.objects.filter(tender__authority=request.user)
    total_bids = my_bids.count()
    
    # Chart Data (Tenders by Status)
    tenders_status = {
        'draft': my_tenders.filter(status='draft').count(),
        'published': active_tenders,
        'closed': my_tenders.filter(status='closed').count(),
        'evaluating': my_tenders.filter(status='evaluating').count(),
    }
    
    # Chart Data (Bids by Status)
    bids_status = {
        'pending': my_bids.filter(status='pending').count(),
        'accepted': my_bids.filter(status='accepted').count(),
        'rejected': my_bids.filter(status='rejected').count(),
    }
    
    recent_tenders = my_tenders.order_by('-created_at')[:5]
    
    # Simulated alerts based on existing data: overdue tenders or un-evaluated bids
    alerts = []
    overdue_tenders = my_tenders.filter(status='published', deadline__lt=timezone.now().date())
    for t in overdue_tenders[:3]:
        alerts.append({'type': 'warning', 'message': f'انتهى أجل إيداع العروض للصفقة: {t.title}', 'date': t.deadline})
        
    context = {
        'total_tenders': total_tenders,
        'active_tenders': active_tenders,
        'total_bids': total_bids,
        'tenders_chart_data': json.dumps(list(tenders_status.values())),
        'bids_chart_data': json.dumps(list(bids_status.values())),
        'recent_tenders': recent_tenders,
        'alerts': alerts,
    }
    return render(request, 'dashboard/authority_dashboard.html', context)

@login_required
def supplier_dashboard(request):
    active_tenders = Tender.objects.filter(status='published').count()
    
    my_bids = Bid.objects.filter(supplier=request.user)
    supplier_bids = my_bids.count()
    won_bids = my_bids.filter(status='accepted').count()
    
    # Chart Data (My Bids by Status)
    my_bids_status = {
        'pending': my_bids.filter(status='pending').count(),
        'accepted': won_bids,
        'rejected': my_bids.filter(status='rejected').count(),
    }
    
    # Smart Recommendations
    recommended_tenders = []
    if request.user.sector:
        recommended_tenders = Tender.objects.filter(
            status='published', 
            sector=request.user.sector
        ).order_by('-created_at')[:4]

    context = {
        'active_tenders': active_tenders,
        'supplier_bids': supplier_bids,
        'won_bids': won_bids,
        'my_bids_chart_data': json.dumps(list(my_bids_status.values())),
        'recommended_tenders': recommended_tenders,
        'user_sector': request.user.sector,
    }
    return render(request, 'dashboard/supplier_dashboard.html', context)

@login_required
def archive_list(request):
    from django.db.models import Q
    from django.utils import timezone
    archived_tenders = Tender.objects.filter(
        Q(status='closed') | Q(deadline__lt=timezone.now().date())
    ).order_by('-updated_at')
    context = {
        'tenders': archived_tenders
    }
    return render(request, 'dashboard/archive.html', context)

@login_required
@permission_required('procurement.view_tender', raise_exception=True)
def authority_reports(request):
    from django.db.models import Sum, Avg, Count, F, ExpressionWrapper, DurationField
    from django.db.models.functions import TruncMonth
    from django.utils import timezone
    
    my_tenders = Tender.objects.filter(authority=request.user)
    total_tenders = my_tenders.count()
    
    # 1. عدد الصفقات حسب الحالة
    tenders_by_status = list(my_tenders.values('status').annotate(count=Count('id')))
    status_counts = {item['status']: item['count'] for item in tenders_by_status}
    
    closed_tenders = status_counts.get('closed', 0)
    
    # 2. مدة المعالجة (للصفقات المغلقة: updated_at - created_at)
    processing_times = my_tenders.filter(status='closed').annotate(
        duration=ExpressionWrapper(F('updated_at') - F('created_at'), output_field=DurationField())
    ).aggregate(avg_duration=Avg('duration'))
    avg_processing_days = processing_times['avg_duration'].days if processing_times['avg_duration'] else 0
    
    # 3. إجمالي عدد العروض المستلمة في صفقات المصلحة
    total_bids = Bid.objects.filter(tender__authority=request.user).count()
    
    # 4. الصفقات المتأخرة (انتهت آجالها ولم تغلق بعد)
    overdue_tenders_count = my_tenders.filter(
        deadline__lt=timezone.now().date()
    ).exclude(status='closed').count()
    
    # 5. أداء الفترة الزمنية (الصفقات حسب الشهر)
    tenders_by_month = list(
        my_tenders.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    month_labels = [t['month'].strftime('%Y-%m') if t['month'] else 'N/A' for t in tenders_by_month]
    month_counts = [t['count'] for t in tenders_by_month]
    
    # 6. بيانات القطاع
    tenders_by_sector = list(my_tenders.values('sector').annotate(count=Count('id')))
    sector_labels = [t['sector'] or 'غير محدد' for t in tenders_by_sector]
    sector_counts = [t['count'] for t in tenders_by_sector]

    # Sum of budgets for closed tenders
    total_budget_spent = my_tenders.filter(status='closed').aggregate(total=Sum('budget'))['total'] or 0
    
    # Average bids per tender
    avg_bids = my_tenders.annotate(bid_count=Count('bids')).aggregate(avg=Avg('bid_count'))['avg'] or 0
    
    context = {
        'total_tenders': total_tenders,
        'closed_tenders': closed_tenders,
        'total_budget_spent': total_budget_spent,
        'avg_bids': round(avg_bids, 1),
        
        # New Metrics
        'tenders_by_status_json': json.dumps(status_counts),
        'avg_processing_days': avg_processing_days,
        'total_bids': total_bids,
        'overdue_tenders_count': overdue_tenders_count,
        
        'month_labels_json': json.dumps(month_labels),
        'month_counts_json': json.dumps(month_counts),
        
        'sector_labels_json': json.dumps(sector_labels),
        'sector_counts_json': json.dumps(sector_counts),
    }
    return render(request, 'dashboard/authority_reports.html', context)

