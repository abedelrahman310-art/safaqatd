from django.urls import path
from . import views
from . import views_admin

app_name = 'dashboard'

urlpatterns = [
    path('authority/', views.authority_dashboard, name='authority'),
    path('supplier/', views.supplier_dashboard, name='supplier'),
    path('archive/', views.archive_list, name='archive'),
    path('regulator/', views_admin.regulator_dashboard, name='regulator'),
    path('regulator/users/', views_admin.regulator_users_list, name='regulator_users'),
    path('regulator/users/<int:user_id>/toggle/', views_admin.toggle_user_status, name='toggle_user_status'),
    path('regulator/audit/', views_admin.regulator_audit_list, name='regulator_audit'),
    path('authority/reports/', views.authority_reports, name='authority_reports'),
]
