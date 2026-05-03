from django.contrib import admin
from .models import LoanProduct, LoanApplication, ApprovalAction, RepaymentSchedule


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'min_amount', 'max_amount', 'interest_rate',
                     'interest_method', 'repayment_frequency', 'is_active']
    list_filter   = ['interest_method', 'repayment_frequency', 'is_active']
    search_fields = ['name', 'code']


class ApprovalActionInline(admin.TabularInline):
    model = ApprovalAction
    extra = 0
    readonly_fields = ['actor', 'action', 'comment', 'created_at']
    can_delete = False


class ScheduleInline(admin.TabularInline):
    model = RepaymentSchedule
    extra = 0
    readonly_fields = ['instalment_number', 'due_date', 'total_due', 'is_paid', 'paid_date']
    can_delete = False


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display  = ['application_number', 'customer', 'product', 'requested_amount',
                     'approved_amount', 'status', 'branch', 'created_at']
    list_filter   = ['status', 'branch', 'product']
    search_fields = ['application_number', 'customer__full_name', 'customer__nin']
    readonly_fields = ['application_number', 'created_at', 'updated_at',
                       'created_by', 'submitted_at']
    inlines = [ApprovalActionInline, ScheduleInline]
    actions = ['mark_written_off']

    @admin.action(description='Mark selected loans as Written Off')
    def mark_written_off(self, request, queryset):
        updated = queryset.filter(status='active').update(status='written_off')
        self.message_user(request, f"{updated} loan(s) written off.")
