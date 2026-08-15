from django.shortcuts import render, redirect

def index(request):
    from apps.procurement.models import Tender
    from django.utils import timezone
    from django.db.models import Count, Sum
    
    # Active live published tenders
    live_tenders = Tender.objects.filter(
        status='published',
        deadline__gte=timezone.now()
    ).select_related('authority').order_by('-created_at')[:6]
    
    total_published_count = Tender.objects.filter(status='published').count()
    total_budget_sum = Tender.objects.filter(status='published').aggregate(Sum('budget'))['budget__sum'] or 0

    return render(request, 'core/landing.html', {
        'live_tenders': live_tenders,
        'total_published_count': total_published_count,
        'total_budget_sum': total_budget_sum,
    })

from django.contrib.auth.decorators import login_required
from .models import Notification

def about(request):
    return render(request, 'core/about.html')

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'core:index'))

@login_required
def notifications_list(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    return render(request, 'core/notifications_list.html', {'all_notifications': notifications})

