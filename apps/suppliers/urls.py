from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.SupplierDashboardView.as_view(), name='dashboard'),
    path('tenders/', views.AvailableTendersListView.as_view(), name='tenders_list'),
    path('tenders/<int:pk>/', views.TenderDetailView.as_view(), name='tender_detail'),
]
