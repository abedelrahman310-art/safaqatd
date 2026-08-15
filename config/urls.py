from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponseForbidden

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')), # Accounts and Registration (Supplier, Authority, Central Admin)
    path('dashboard/', include('apps.dashboard.urls')),
    path('suppliers/', include('apps.suppliers.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('procurement/', include('apps.procurement.urls')),
    path('ai/', include('apps.ai.urls')),
    path('ai/assistant/', include('apps.ai_assistant.urls')),
    path('ai/regulator/', include('apps.ai_regulator.urls')),
    path('ai/authority/', include('apps.ai_authority.urls')),
    path('ai/supplier/', include('apps.ai_supplier.urls')),
    path('health/', include('apps.system_health.urls')),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw.js'),
    # Block direct access to secure bids files via media URL (both in dev and prod fallback)
    re_path(r'^media/bids/secure/.*', lambda request, **kwargs: HttpResponseForbidden("الوصول المباشر للملفات السرية غير مصرح به. الرجاء استخدام دالة التحميل المؤمنة.")),
    # Block direct access to tender documents
    re_path(r'^media/tenders/documents/.*', lambda request, **kwargs: HttpResponseForbidden("الوصول المباشر لدفاتر الشروط غير مصرح به. الرجاء استخدام دالة التحميل المؤمنة.")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
