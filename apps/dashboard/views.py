from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from apps.procurement.models import Tender, Bid
from apps.accounts.models import User
import json

@login_required
def authority_dashboard(request):
    total_tenders = Tender.objects.count()
    active_tenders = Tender.objects.filter(status='published').count()
    total_bids = Bid.objects.count()
    
    # Chart Data (Tenders by Status)
    tenders_status = {
        'draft': Tender.objects.filter(status='draft').count(),
        'published': active_tenders,
        'closed': Tender.objects.filter(status='closed').count(),
        'evaluating': Tender.objects.filter(status='evaluating').count(),
    }
    
    # Chart Data (Bids by Status)
    bids_status = {
        'pending': Bid.objects.filter(status='pending').count(),
        'accepted': Bid.objects.filter(status='accepted').count(),
        'rejected': Bid.objects.filter(status='rejected').count(),
    }
    
    context = {
        'total_tenders': total_tenders,
        'active_tenders': active_tenders,
        'total_bids': total_bids,
        'tenders_chart_data': json.dumps(list(tenders_status.values())),
        'bids_chart_data': json.dumps(list(bids_status.values())),
    }
    return render(request, 'dashboard/authority_dashboard.html', context)

@login_required
def supplier_dashboard(request):
    active_tenders = Tender.objects.filter(status='published').count()
    
    my_bids = Bid.objects.filter(supplier_name=request.user.full_name) if request.user.full_name else Bid.objects.none()
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
def authority_reports(request):
    if request.user.role != 'authority':
        return redirect('dashboard:supplier')
        
    my_tenders = Tender.objects.filter(authority=request.user)
    total_tenders = my_tenders.count()
    closed_tenders = my_tenders.filter(status='closed').count()
    
    from django.db.models import Sum, Avg, Count
    # Sum of budgets for closed tenders
    total_budget_spent = my_tenders.filter(status='closed').aggregate(total=Sum('budget'))['total'] or 0
    
    # Average bids per tender
    avg_bids = my_tenders.annotate(bid_count=Count('bids')).aggregate(avg=Avg('bid_count'))['avg'] or 0
    
    context = {
        'total_tenders': total_tenders,
        'closed_tenders': closed_tenders,
        'total_budget_spent': total_budget_spent,
        'avg_bids': round(avg_bids, 1)
    }
    return render(request, 'dashboard/authority_reports.html', context)

