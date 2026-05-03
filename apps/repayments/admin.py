from django.contrib import admin
from .models import Repayment, PenaltyWaiver, LoanRestructure

@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display  = ['loan', 'amount', 'channel', 'payment_date', 'recorded_by', 'is_reversed']
    list_filter   = ['channel', 'is_reversed']
    search_fields = ['loan__application_number', 'loan__customer__full_name', 'reference']
    readonly_fields = ['created_at', 'recorded_by']

@admin.register(PenaltyWaiver)
class WaiverAdmin(admin.ModelAdmin):
    list_display = ['loan', 'waived_amount', 'approved_by', 'created_at']

@admin.register(LoanRestructure)
class RestructureAdmin(admin.ModelAdmin):
    list_display = ['loan', 'old_period_months', 'new_period_months', 'approved_by', 'created_at']
