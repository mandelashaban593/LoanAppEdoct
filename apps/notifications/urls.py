from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification

app_name = 'notifications'


@login_required
def notification_list(request):
    notifs = request.user.notifications.all()[:100]
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'notifications': notifs})


@login_required
def mark_read(request, pk):
    Notification.objects.filter(pk=pk, recipient=request.user).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:home'))


urlpatterns = [
    path('',          notification_list, name='list'),
    path('<int:pk>/read/', mark_read,    name='mark_read'),
]
