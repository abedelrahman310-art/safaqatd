from django.urls import path
from apps.ai_authority import views

app_name = 'ai_authority'

urlpatterns = [
    path('rfp-generator/', views.rfp_generator_view, name='rfp_generator'),
    path('rfp-generator/<int:rfp_id>/', views.rfp_generator_view, name='rfp_detail'),
    path('bid-evaluator/', views.bid_evaluation_view, name='bid_evaluator'),
    path('bid-evaluator/<int:tender_id>/', views.bid_evaluation_view, name='bid_evaluator_detail'),
    path('price-estimator/', views.price_estimator_view, name='price_estimator'),
]
