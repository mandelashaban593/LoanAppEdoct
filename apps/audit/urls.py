from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AuditLog

app_name = 'audit'

@login_required
def audit_log_list(request):
    if not (request.user.is_sys_admin or request.user.is_auditor):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access denied.")
    logs = AuditLog.objects.select_related('user').all()[:500]
    return render(request, 'audit/log_list.html', {'logs': logs})

urlpatterns = [
    path('logs/', audit_log_list, name='logs'),
]
