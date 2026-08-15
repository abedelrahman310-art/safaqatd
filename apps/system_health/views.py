from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from .services import SystemHealthService

@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def health_dashboard_view(request):
    """Render the System Health & Observability Dashboard."""
    health_data = SystemHealthService.get_full_system_status()
    context = {
        'health': health_data,
        'title': 'غرفة العمليات ومراقبة صحة النظام السيادي',
    }
    return render(request, 'system_health/health_dashboard.html', context)


@login_required
@permission_required('accounts.view_central_dashboard', raise_exception=True)
def health_status_api(request):
    """API Endpoint returning JSON status for real-time live pulse checking."""
    health_data = SystemHealthService.get_full_system_status()
    # Serialize for JSON
    response_data = {
        'timestamp': health_data['timestamp'].isoformat(),
        'overall_status': health_data['overall_status'],
        'overall_label': health_data['overall_label'],
        'db_latency_ms': health_data['db']['latency_ms'],
        'db_status': health_data['db']['status'],
        'crypto_status': health_data['crypto']['status'],
        'ai_status': health_data['ai']['status'],
        'security_status': health_data['security']['status'],
        'storage_used_pct': health_data['storage'].get('used_pct', 0),
        'storage_free_gb': health_data['storage'].get('free_gb', 0),
        'total_users': health_data['total_users'],
        'active_tenders': health_data['active_tenders'],
    }
    return JsonResponse(response_data)
