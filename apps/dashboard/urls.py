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
    path('regulator/users/<int:user_id>/toggle/', views_admin.toggle_user_status, name='toggle_user_status'),
    path('regulator/audit/', views_admin.regulator_audit_list, name='regulator_audit'),
    path('regulator/audit/<int:tender_id>/', views_admin.regulator_audit_detail, name='regulator_audit_detail'),
    path('regulator/planning/', views_admin.planning_department_view, name='regulator_planning'),
    path('regulator/health/', views_admin.system_health_view, name='system_health'),
    
    # New Regulator URLs
    path('regulator/authorities/', views_admin.regulator_authorities_view, name='regulator_authorities'),
    path('regulator/suppliers/', views_admin.regulator_suppliers_view, name='regulator_suppliers'),
    path('regulator/tenders/', views_admin.regulator_tenders_view, name='regulator_tenders'),
    path('regulator/tenders/<int:tender_id>/freeze/', views_admin.freeze_tender_view, name='regulator_freeze_tender'),
    path('regulator/tenders/<int:tender_id>/ledger/', views_admin.fetch_blockchain_ledger_view, name='regulator_fetch_ledger'),
    path('regulator/audit_log/', views_admin.regulator_audit_log_view, name='regulator_audit_log'),
    path('regulator/documents/', views_admin.regulator_documents_view, name='regulator_documents'),
    path('regulator/notifications/', views_admin.regulator_notifications_view, name='regulator_notifications'),
    path('regulator/support/', views_admin.regulator_support_view, name='regulator_support'),
    
    path('authority/reports/', views.authority_reports, name='authority_reports'),
]
