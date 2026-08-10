from django.db.models import Count, Q
from django.utils import timezone

from apps.procurement.models import Tender

def get_visible_tenders(user):
    """صلاحيات المستخدم -> QuerySet المسموح"""
    return Tender.objects.visible_to(user).filter(is_deleted=False)

def apply_regulator_filters(queryset, filters):
    """QuerySet المسموح -> الفلاتر"""
    filters = filters or {}
    if filters.get("status"):
        queryset = queryset.filter(status=filters["status"])
    if filters.get("wilaya"):
        queryset = queryset.filter(wilaya=filters["wilaya"])
    if filters.get("date_from"):
        queryset = queryset.filter(created_at__date__gte=filters["date_from"])
    if filters.get("date_to"):
        queryset = queryset.filter(created_at__date__lte=filters["date_to"])
    if filters.get("sector"):
        queryset = queryset.filter(sector__icontains=filters["sector"])
    return queryset

def get_regulator_statistics(queryset):
    """الفلاتر -> الإحصاءات"""
    today = timezone.localdate()
    
    # 1. Alarms: overdue or evaluating with no bids or some conditions. 
    # Since we need "جدول الإنذارات: صفقات متأخرة، صفقات بلا عروض، عروض ناقصة الوثائق"
    # Overdue
    overdue_qs = queryset.filter(deadline__lt=today, status__in=["published", "evaluating"])
    # (Assuming we have related bids, but since we don't have exact models for all, we will return overdue for now)
    
    # 2. Charts
    import json
    from django.db.models.functions import TruncMonth
    
    by_status = list(queryset.values("status").annotate(total=Count("id")).order_by("status"))
    by_wilaya = list(queryset.values("wilaya").annotate(total=Count("id")).order_by("-total")[:10])
    by_month = list(queryset.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Count('id')).order_by('month'))
    
    # Convert dates to string for JSON serialization
    for item in by_month:
        if item['month']:
            item['month'] = item['month'].strftime('%Y-%m')
            
    # Tenders for detailed table
    recent_tenders = queryset.order_by('-created_at')
    
    # Audit trail (mocked with simple recent tenders log for now since no AuditLog model exists)
    audit_trail = [] # Could fetch from LogEntry if needed
    
    return {
        "total": queryset.count(),
        "published": queryset.filter(status="published").count(),
        "under_evaluation": queryset.filter(status="evaluating").count(),
        "closed": queryset.filter(status="closed").count(),
        "overdue": overdue_qs.count(),
        "by_status": by_status,
        "by_status_json": json.dumps(by_status),
        "by_wilaya_json": json.dumps(by_wilaya),
        "by_month_json": json.dumps(by_month),
        "alarms": overdue_qs[:10],
        "tenders": recent_tenders,
        "audit_trail": audit_trail,
    }

def get_regulator_summary(user, filters=None):
    """العرض (يجمع الخطوات السابقة للوحة القيادة)"""
    queryset = get_visible_tenders(user)
    filtered_queryset = apply_regulator_filters(queryset, filters)
    return get_regulator_statistics(filtered_queryset)
