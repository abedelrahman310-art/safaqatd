from django.urls import path
from apps.ai_regulator import views

app_name = 'ai_regulator'

urlpatterns = [
    path('radar/', views.radar_dashboard_view, name='radar_dashboard'),
    path('rfp-auditor/', views.rfp_auditor_view, name='rfp_auditor'),
    path('rfp-auditor/<int:tender_id>/', views.rfp_auditor_view, name='rfp_auditor_detail'),
    path('legal-copilot/', views.legal_copilot_view, name='legal_copilot'),
]
