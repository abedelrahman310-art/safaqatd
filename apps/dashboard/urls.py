from django.urls import path
from . import views
from . import views_admin

app_name = 'dashboard'

urlpatterns = [
    path('authority/', views.authority_dashboard, name='authority'),
    path('supplier/', views.supplier_dashboard, name='supplier'),
    path('archive/', views.archive_list, name='archive'),
    path('regulator/', views_admin.RegulatorDashboardView.as_view(), name='regulator'),
    path('regulator/export/csv/', views_admin.export_regulator_csv, name='export_regulator_csv'),
    path('regulator/export/pdf/', views_admin.export_regulator_pdf, name='export_regulator_pdf'),
    path('regulator/users/', views_admin.regulator_users_list, name='regulator_users'),
    path('regulator/roles/', views_admin.platform_roles_view, name='regulator_roles'),
    path('regulator/users/<int:user_id>/toggle/', views_admin.toggle_user_status, name='toggle_user_status'),
    path('regulator/audit/', views_admin.regulator_audit_list, name='regulator_audit'),
    path('regulator/audit/<int:tender_id>/', views_admin.regulator_audit_detail, name='regulator_audit_detail'),
    path('regulator/planning/', views_admin.planning_department_view, name='regulator_planning'),
    path('authority/reports/', views.authority_reports, name='authority_reports'),
]
