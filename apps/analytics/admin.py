from django.contrib import admin
from .models import SmartAlert, DataQualityIssue

@admin.register(SmartAlert)
class SmartAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'alert_type', 'is_resolved', 'created_at')
    list_filter = ('severity', 'is_resolved', 'alert_type')
    search_fields = ('title', 'description', 'related_tender__title')

@admin.register(DataQualityIssue)
class DataQualityIssueAdmin(admin.ModelAdmin):
    list_display = ('issue_type', 'related_tender', 'field_name', 'is_fixed', 'created_at')
    list_filter = ('issue_type', 'is_fixed')
    search_fields = ('description', 'related_tender__title', 'field_name')
