from django.contrib import admin
from .models import Customer, CustomerDocument, Guarantor, Collateral


class DocumentInline(admin.TabularInline):
    model = CustomerDocument
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']


class GuarantorInline(admin.TabularInline):
    model = Guarantor
    extra = 0


class CollateralInline(admin.TabularInline):
    model = Collateral
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'nin', 'primary_phone', 'district',
                     'customer_type', 'branch', 'is_blacklisted', 'created_at']
    list_filter   = ['customer_type', 'branch', 'is_blacklisted', 'gender']
    search_fields = ['full_name', 'nin', 'primary_phone', 'mtn_momo_number']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [DocumentInline, GuarantorInline, CollateralInline]
    fieldsets = (
        ('Identity', {'fields': ('full_name', 'nin', 'date_of_birth', 'gender',
                                  'marital_status', 'dependants')}),
        ('Contact',  {'fields': ('primary_phone', 'alternative_phone', 'email')}),
        ('Address',  {'fields': ('district', 'village_lc1', 'physical_address',
                                  'gps_latitude', 'gps_longitude')}),
        ('Next of Kin', {'fields': ('next_of_kin_name', 'next_of_kin_phone',
                                     'next_of_kin_relation')}),
        ('Employment', {'fields': ('customer_type', 'employer_business', 'occupation',
                                    'monthly_income', 'other_income', 'monthly_expenses',
                                    'existing_loans')}),
        ('Banking',  {'fields': ('bank_name', 'bank_account', 'mtn_momo_number',
                                  'airtel_money_number')}),
        ('KYC Docs', {'fields': ('photo', 'id_front', 'id_back')}),
        ('Blacklist',{'fields': ('is_blacklisted', 'blacklist_reason',
                                  'blacklisted_by', 'blacklisted_at')}),
        ('Meta',     {'fields': ('branch', 'created_by', 'created_at', 'updated_at')}),
    )
