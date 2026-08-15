from django.contrib import admin
from .models import Tender, Bid, AnnualBudget, PlannedProject, Award, Contract, ContractAmendment

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

@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ('decision_reference', 'tender', 'awarded_by', 'awarded_amount', 'status', 'awarded_at')
    list_filter = ('status', 'created_at')

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'title', 'supplier', 'authority', 'status', 'total_value')
    list_filter = ('status', 'currency', 'created_at')

@admin.register(ContractAmendment)
class ContractAmendmentAdmin(admin.ModelAdmin):
    list_display = ('amendment_number', 'contract', 'amendment_type', 'status', 'submitted_by')
    list_filter = ('amendment_type', 'status', 'created_at')
