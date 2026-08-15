from django.urls import path
from .views import ai_assistant_view, secure_ai_assistant_view

app_name = 'ai_assistant'

urlpatterns = [
    path('guide/', ai_assistant_view, name='guide'),
    path('secure/', secure_ai_assistant_view, name='secure'),
]
