from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    path('',            views.report_dashboard,   name='dashboard'),
    path('active/',     views.active_loans_report, name='active_loans'),
    path('arrears/',    views.arrears_report,      name='arrears'),
    path('portfolio/',  views.portfolio_summary,   name='portfolio'),
    path('defaulters/', views.defaulters_report,   name='defaulters'),
]
