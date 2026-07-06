from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('evaluate/tender/<int:tender_id>/', views.evaluate_bids_view, name='evaluate_bids'),
    path('draft/tender/', views.draft_tender_view, name='draft_tender'),
    path('generate-cahier/<int:tender_id>/', views.generate_cahier_view, name='generate_cahier'),
    path('chat/', views.chatbot_view, name='chat'),
    path('generate-smart-bid/<int:tender_id>/', views.generate_smart_bid_view, name='generate_smart_bid'),
]
