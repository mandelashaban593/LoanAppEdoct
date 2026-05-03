# apps/accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.audit.utils import log_action
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            user_obj = None

        if user_obj and user_obj.is_account_locked:
            messages.error(request,
                "Your account is locked after too many failed attempts. Contact your administrator.")
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=username, password=password)
        if user:
            user.reset_login_attempts()
            login(request, user)
            log_action(user, 'login', None, ip=_get_ip(request))
            if user.must_change_password:
                return redirect('accounts:change_password')
            return redirect('dashboard:home')
        else:
            if user_obj:
                user_obj.record_failed_login()
            messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        log_action(request.user, 'logout', None, ip=_get_ip(request))
    logout(request)
    return redirect('accounts:login')


@login_required
def change_password(request):
    if request.method == 'POST':
        new_pw  = request.POST.get('new_password', '')
        confirm = request.POST.get('confirm_password', '')
        if len(new_pw) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        elif new_pw != confirm:
            messages.error(request, "Passwords do not match.")
        elif not any(c.isdigit() for c in new_pw):
            messages.error(request, "Password must contain at least one number.")
        else:
            request.user.set_password(new_pw)
            request.user.must_change_password = False
            request.user.save()
            messages.success(request, "Password changed successfully. Please log in again.")
            return redirect('accounts:login')
    return render(request, 'accounts/change_password.html')


def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')


# apps/accounts/context_processors.py
def user_role(request):
    if request.user.is_authenticated:
        return {'user_role': request.user.role,
                'user_branch': request.user.branch}
    return {}
