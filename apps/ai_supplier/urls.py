from django.urls import path
from apps.ai_supplier import views

app_name = 'ai_supplier'

urlpatterns = [
    path('recommendations/', views.tender_recommendations_view, name='recommendations'),
    path('rfp-summary/', views.rfp_quick_summary_view, name='rfp_summary'),
    path('rfp-summary/<int:tender_id>/', views.rfp_quick_summary_view, name='rfp_summary_detail'),
    path('readiness-check/', views.bid_readiness_check_view, name='readiness_check'),
    path('readiness-check/<int:tender_id>/', views.bid_readiness_check_view, name='readiness_check_detail'),
]
