# apps/accounts/dashboard_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from apps.loans.models import LoanApplication
from apps.repayments.models import Repayment
from apps.customers.models import Customer
from datetime import date


@login_required
def dashboard_home(request):
    user = request.user
    today = date.today()

    def qs_base():
        qs = LoanApplication.objects.all()
        if not user.sees_all_branches and user.branch:
            qs = qs.filter(branch=user.branch)
        return qs

    loans = qs_base()

    # KPIs
    active_loans       = loans.filter(status=LoanApplication.STATUS_ACTIVE)
    portfolio_value    = active_loans.aggregate(s=Sum('total_repayable'))['s'] or 0
    outstanding        = sum(l.outstanding_balance for l in active_loans[:500])
    disbursed_today    = loans.filter(
        status__in=[LoanApplication.STATUS_ACTIVE, LoanApplication.STATUS_DISBURSED],
        disbursed_at__date=today)
    disbursed_today_val = disbursed_today.aggregate(s=Sum('disbursed_amount'))['s'] or 0

    repayments_today   = Repayment.objects.filter(payment_date=today, is_reversed=False)
    if not user.sees_all_branches and user.branch:
        repayments_today = repayments_today.filter(loan__branch=user.branch)
    collected_today    = repayments_today.aggregate(s=Sum('amount'))['s'] or 0

    pending_approval   = loans.filter(
        status__in=[LoanApplication.STATUS_SUBMITTED, LoanApplication.STATUS_REVIEWING]).count()
    overdue_loans      = [l for l in active_loans if l.is_overdue]

    # Recent activity
    recent_loans = loans.select_related('customer','product').order_by('-created_at')[:8]

    context = {
        'active_count':       active_loans.count(),
        'portfolio_value':    portfolio_value,
        'outstanding':        outstanding,
        'disbursed_today':    disbursed_today_val,
        'disbursed_today_ct': disbursed_today.count(),
        'collected_today':    collected_today,
        'pending_approval':   pending_approval,
        'overdue_count':      len(overdue_loans),
        'recent_loans':       recent_loans,
        'total_customers':    Customer.objects.filter(
            *([{'branch': user.branch}] if not user.sees_all_branches else [])).count(),
    }
    return render(request, 'dashboard/home.html', context)
