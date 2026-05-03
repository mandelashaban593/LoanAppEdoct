# apps/reports/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from apps.loans.models import LoanApplication, RepaymentSchedule
from apps.repayments.models import Repayment
from apps.customers.models import Customer
from apps.audit.utils import log_action


def _branch_filter(user, qs, field='branch'):
    if user.sees_all_branches:
        return qs
    return qs.filter(**{field: user.branch})


@login_required
def report_dashboard(request):
    return render(request, 'reports/dashboard.html')


@login_required
def active_loans_report(request):
    qs = _branch_filter(request.user,
         LoanApplication.objects.filter(status=LoanApplication.STATUS_ACTIVE)
         .select_related('customer', 'product', 'branch'))
    _apply_filters(request, qs)
    total_portfolio = qs.aggregate(s=Sum('total_repayable'))['s'] or 0
    log_action(request.user, 'export', None, after={'report': 'active_loans'})
    return render(request, 'reports/active_loans.html', {
        'loans': qs, 'total_portfolio': total_portfolio,
        'report_date': date.today(),
    })


@login_required
def arrears_report(request):
    today = date.today()
    overdue_schedules = RepaymentSchedule.objects.filter(
        due_date__lt=today, is_paid=False
    ).select_related('loan__customer', 'loan__product', 'loan__branch')
    if not request.user.sees_all_branches:
        overdue_schedules = overdue_schedules.filter(loan__branch=request.user.branch)
    total_overdue = overdue_schedules.aggregate(
        s=Sum('total_due'))['s'] or 0
    log_action(request.user, 'export', None, after={'report': 'arrears'})
    return render(request, 'reports/arrears.html', {
        'schedules': overdue_schedules[:500],
        'total_overdue': total_overdue,
        'report_date': date.today(),
    })


@login_required
def portfolio_summary(request):
    loans = LoanApplication.objects.all()
    if not request.user.sees_all_branches:
        loans = loans.filter(branch=request.user.branch)
    summary = {
        'active': loans.filter(status=LoanApplication.STATUS_ACTIVE).aggregate(
            count=Count('id'), total=Sum('total_repayable')),
        'disbursed_month': loans.filter(
            disbursed_at__month=date.today().month,
            disbursed_at__year=date.today().year).aggregate(
            count=Count('id'), total=Sum('disbursed_amount')),
        'closed': loans.filter(status=LoanApplication.STATUS_CLOSED).aggregate(
            count=Count('id'), total=Sum('total_repayable')),
        'written_off': loans.filter(status=LoanApplication.STATUS_WRITTEN_OFF).aggregate(
            count=Count('id'), total=Sum('total_repayable')),
        'pending': loans.filter(status__in=[
            LoanApplication.STATUS_SUBMITTED,
            LoanApplication.STATUS_REVIEWING]).count(),
    }
    repayments = Repayment.objects.filter(is_reversed=False)
    if not request.user.sees_all_branches:
        repayments = repayments.filter(loan__branch=request.user.branch)
    summary['total_collected'] = repayments.aggregate(s=Sum('amount'))['s'] or 0
    summary['interest_income'] = repayments.aggregate(s=Sum('interest_portion'))['s'] or 0
    summary['penalty_income']  = repayments.aggregate(s=Sum('penalty_portion'))['s'] or 0
    log_action(request.user, 'export', None, after={'report': 'portfolio_summary'})
    return render(request, 'reports/portfolio_summary.html', {
        'summary': summary, 'report_date': date.today(),
    })


@login_required
def defaulters_report(request):
    today = date.today()
    cutoff = today - timedelta(days=90)
    overdue = RepaymentSchedule.objects.filter(
        due_date__lte=cutoff, is_paid=False
    ).select_related('loan__customer', 'loan__branch')
    if not request.user.sees_all_branches:
        overdue = overdue.filter(loan__branch=request.user.branch)
    loan_ids = overdue.values_list('loan_id', flat=True).distinct()
    loans = LoanApplication.objects.filter(pk__in=loan_ids).select_related('customer')
    log_action(request.user, 'export', None, after={'report': 'defaulters'})
    return render(request, 'reports/defaulters.html', {
        'loans': loans, 'report_date': today,
    })


def _apply_filters(request, qs):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    return qs
