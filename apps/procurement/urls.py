from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    path('tenders/', views.tender_list, name='tender_list'),
    path('authority/tenders/', views.authority_tender_list, name='authority_tender_list'),
    path('authority/tenders/create/', views.tender_create, name='tender_create'),
    path('authority/tenders/<int:tender_id>/edit/', views.tender_edit, name='tender_edit'),
    path('authority/tenders/<int:tender_id>/delete/', views.tender_delete, name='tender_delete'),
    path('authority/tenders/<int:tender_id>/bids/', views.authority_tender_bids, name='authority_tender_bids'),
    path('authority/tenders/<int:tender_id>/bids/open/', views.open_tender_bids, name='open_tender_bids'),
    path('authority/bids/<int:bid_id>/update/<str:status>/', views.bid_update_status, name='bid_update_status'),
    path('authority/bids/<int:bid_id>/rate/', views.rate_supplier, name='rate_supplier'),
    
    # Secure Download
    path('bids/<int:bid_id>/download/<str:document_type>/', views.secure_bid_download, name='secure_bid_download'),
    
    path('tenders/<int:tender_id>/bid/', views.bid_create, name='bid_create'),
    path('tenders/<int:tender_id>/', views.tender_detail, name='tender_detail'),
    path('tenders/<int:tender_id>/report/', views.generate_report_view, name='generate_report_view'),
    path('tenders/<int:tender_id>/payment/', views.payment_checkout, name='payment_checkout'),
    path('tenders/<int:tender_id>/satim/', views.satim_gateway_view, name='satim_gateway'),
    path('tenders/<int:tender_id>/satim/otp/', views.satim_otp_view, name='satim_otp'),
    path('tenders/<int:tender_id>/process_payment/', views.process_payment, name='process_payment'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('evaluation/', views.tender_evaluation_list, name='tender_evaluation_list'),
    path('tenders/<int:tender_id>/pdf/', views.download_tender_pdf, name='download_tender_pdf'),
    # Appeals URLs
    path('appeals/submit/<int:bid_id>/', views.submit_appeal, name='submit_appeal'),
    path('appeals/authority/', views.authority_appeals, name='authority_appeals'),
    
    # Committee URLs
    path('tenders/<int:tender_id>/committee/', views.manage_committee, name='manage_committee'),
    path('tenders/<int:tender_id>/committee/sign/', views.sign_evaluation, name='sign_evaluation'),
    
    # Virtual Opening Room
    path('tenders/<int:tender_id>/opening-room/', views.virtual_opening_room, name='virtual_opening_room'),
    path('tenders/<int:tender_id>/live-opening/', views.supplier_live_opening, name='supplier_live_opening'),
]
