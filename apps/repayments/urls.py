# apps/repayments/urls.py
from django.urls import path
from . import views

app_name = 'repayments'
urlpatterns = [
    path('loan/<int:loan_pk>/pay/',         views.repayment_create,  name='create'),
    path('loan/<int:loan_pk>/waiver/',      views.waiver_create,     name='waiver'),
    path('loan/<int:loan_pk>/restructure/', views.restructure_create, name='restructure'),
]
