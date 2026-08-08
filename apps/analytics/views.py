import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.db.models import Sum, Avg, Count, F, Q
from apps.procurement.models import Tender, Bid
from django.contrib.auth import get_user_model
from datetime import timedelta
import random

User = get_user_model()

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def analytics_dashboard(request):
    """Main Analytics Dashboard View"""
    # Calculate basic KPIs directly for the context
    now = timezone.now()
    
    total_tenders = Tender.objects.count()
    active_tenders = Tender.objects.filter(status__in=['published', 'evaluating']).count()
    completed_tenders = Tender.objects.filter(status='closed').count()
    late_tenders = Tender.objects.filter(deadline__lt=now.date()).exclude(status='closed').count()
    
    # Financial Value
    total_value = Tender.objects.aggregate(total=Sum('budget'))['total'] or 0
    
    # Average Processing Time (Mocked for MVP as we don't track full stage dates yet)
    avg_processing_days = 14 
    
    # Data Quality (Percentage of Tenders with Sector and Wilaya)
    complete_data_tenders = Tender.objects.filter(sector__isnull=False, wilaya__isnull=False).count()
    data_quality_pct = int((complete_data_tenders / total_tenders * 100) if total_tenders > 0 else 0)
    
    # Completion Rate (Mocked)
    completion_rate = int((completed_tenders / total_tenders * 100) if total_tenders > 0 else 0)

    context = {
        'kpi_total': total_tenders,
        'kpi_active': active_tenders,
        'kpi_completed': completed_tenders,
        'kpi_late': late_tenders,
        'kpi_value': total_value,
        'kpi_avg_days': avg_processing_days,
        'kpi_quality': data_quality_pct,
        'kpi_completion': completion_rate,
        'last_updated': now.strftime("%Y-%m-%d %H:%M"),
    }
    return render(request, 'analytics/analytics_dashboard.html', context)


@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def get_chart_data(request):
    """API Endpoint to fetch data for charts"""
    # 1. Tender Evolution over time (Last 6 months Mocked for demo)
    months = ['جانفي', 'فيفري', 'مارس', 'أفريل', 'ماي', 'جوان']
    evolution_data = {
        'labels': months,
        'new_tenders': [random.randint(10, 50) for _ in range(6)],
        'completed_tenders': [random.randint(5, 40) for _ in range(6)],
        'late_tenders': [random.randint(0, 15) for _ in range(6)]
    }

    # 2. Status Distribution
    status_counts = Tender.objects.values('status').annotate(count=Count('id'))
    status_map = {'draft': 'مسودة', 'published': 'منشورة', 'evaluating': 'قيد التقييم', 'closed': 'مغلقة'}
    status_data = {
        'labels': [status_map.get(s['status'], s['status']) for s in status_counts],
        'data': [s['count'] for s in status_counts]
    }

    # 3. Value by Sector
    sector_counts = Tender.objects.values('sector').annotate(total_budget=Sum('budget'))
    sector_data = {
        'labels': [s['sector'] or 'غير محدد' for s in sector_counts],
        'data': [float(s['total_budget'] or 0) for s in sector_counts]
    }

    return JsonResponse({
        'evolution': evolution_data,
        'status': status_data,
        'sector': sector_data,
    })

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def ask_your_data(request):
    """Mock Gemini API endpoint for 'Ask your data'"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            
            # Here we would normally call Google Gemini with contextual data.
            # For the MVP, we return a mock intelligent response.
            response_text = f"بناءً على البيانات المتاحة، لاختبار الذكاء الاصطناعي لسؤالك: '{question}'... يبدو أن متوسط مدة المعالجة مستقر، مع وجود تأخير طفيف في قطاع الأشغال العمومية. أنصح بمراجعة الصفقات المتأخرة في هذا القطاع."
            
            return JsonResponse({'answer': response_text, 'source': 'Gemini 2.5 Flash', 'confidence': 'عالية'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
