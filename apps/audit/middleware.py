from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.conf import settings


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user.last_active = timezone.now()
            request.user.save(update_fields=['last_active'])
        return self.get_response(request)
