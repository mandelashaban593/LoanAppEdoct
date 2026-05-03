from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'district', 'is_head_office', 'is_active']
    list_filter   = ['is_head_office', 'is_active']
    search_fields = ['name', 'code', 'district']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'get_full_name', 'role', 'branch', 'is_active',
                     'failed_login_attempts', 'locked_at']
    list_filter   = ['role', 'branch', 'is_active', 'must_change_password']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Branch', {'fields': ('role', 'branch', 'phone')}),
        ('Security',      {'fields': ('must_change_password', 'failed_login_attempts', 'locked_at')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Branch', {'fields': ('role', 'branch', 'phone', 'first_name', 'last_name')}),
    )
    actions = ['unlock_accounts', 'force_password_change']

    @admin.action(description='Unlock selected accounts')
    def unlock_accounts(self, request, queryset):
        queryset.update(failed_login_attempts=0, locked_at=None)
        self.message_user(request, f"{queryset.count()} account(s) unlocked.")

    @admin.action(description='Force password change on next login')
    def force_password_change(self, request, queryset):
        queryset.update(must_change_password=True)
        self.message_user(request, f"{queryset.count()} user(s) flagged.")
