# apps/loans/urls.py
from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('',                    views.loan_list,    name='list'),
    path('create/',             views.loan_create,  name='create'),
    path('<int:pk>/',           views.loan_detail,  name='detail'),
    path('<int:pk>/edit/',      views.loan_edit,    name='edit'),
    path('<int:pk>/submit/',    views.loan_submit,  name='submit'),
    path('<int:pk>/review/',    views.loan_review,  name='review'),
    path('<int:pk>/approve/',   views.loan_approve, name='approve'),
    path('<int:pk>/reject/',    views.loan_reject,  name='reject'),
    path('<int:pk>/return/',    views.loan_return,  name='return'),
    path('<int:pk>/disburse/',  views.loan_disburse,name='disburse'),
]
