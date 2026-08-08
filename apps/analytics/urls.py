from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('api/charts/', views.get_chart_data, name='api_charts'),
    path('api/ask/', views.ask_your_data, name='api_ask'),
]
