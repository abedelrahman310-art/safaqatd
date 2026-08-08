from django.contrib import admin
from .models import Tender, Bid, AnnualBudget, PlannedProject

@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ('title', 'budget', 'status', 'authority')
    list_filter = ('status', 'tender_type')

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('tender', 'supplier_name', 'financial_offer', 'status')
    list_filter = ('status',)

@admin.register(AnnualBudget)
class AnnualBudgetAdmin(admin.ModelAdmin):
    list_display = ('year', 'sector', 'total_budget', 'authority')
    list_filter = ('year', 'sector')

@admin.register(PlannedProject)
class PlannedProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'budget', 'estimated_value', 'expected_launch_date', 'is_launched')
    list_filter = ('is_launched', 'expected_launch_date')
