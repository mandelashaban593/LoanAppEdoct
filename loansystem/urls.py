from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.accounts.dashboard_urls', namespace='dashboard')),
    path('customers/', include('apps.customers.urls', namespace='customers')),
    path('loans/', include('apps.loans.urls', namespace='loans')),
    path('repayments/', include('apps.repayments.urls', namespace='repayments')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('audit/', include('apps.audit.urls', namespace='audit')),
    path('', include('apps.accounts.dashboard_urls')),
    path('api/', include('api.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Loan Management System — Admin"
admin.site.site_title = "LMS Admin"
admin.site.index_title = "System Administration"
