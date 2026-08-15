from django.urls import path
from . import views

app_name = 'system_health'

urlpatterns = [
    path('dashboard/', views.health_dashboard_view, name='dashboard'),
    path('api/status/', views.health_status_api, name='api_status'),
]
