# apps/repayments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Repayment, PenaltyWaiver, LoanRestructure
from apps.loans.models import LoanApplication, RepaymentSchedule
from apps.audit.utils import log_action
from .forms import RepaymentForm, WaiverForm, RestructureForm
from decimal import Decimal


@login_required
def repayment_create(request, loan_pk):
    loan = get_object_or_404(LoanApplication, pk=loan_pk)
    if loan.status != LoanApplication.STATUS_ACTIVE:
        messages.error(request, "Repayments can only be recorded for Active loans.")
        return redirect('loans:detail', pk=loan_pk)

    if request.method == 'POST':
        form = RepaymentForm(request.POST, loan=loan)
        if form.is_valid():
            with transaction.atomic():
                repayment = form.save(commit=False)
                repayment.loan = loan
                repayment.recorded_by = request.user

                # Allocate: penalty → interest → principal
                amount = repayment.amount
                schedule = loan.schedule.filter(is_paid=False).order_by('instalment_number')
                penalty_total  = sum(s.penalty_due for s in schedule)
                interest_total = sum(s.interest_due - s.amount_paid for s in schedule
                                     if s.amount_paid < s.interest_due)

                repayment.penalty_portion  = min(amount, penalty_total)
                amount -= repayment.penalty_portion
                repayment.interest_portion = min(amount, interest_total)
                amount -= repayment.interest_portion
                repayment.principal_portion = amount
                repayment.save()

                # Mark schedule items as paid
                remaining = repayment.amount
                for item in schedule:
                    if remaining <= 0:
                        break
                    if remaining >= item.balance_due:
                        remaining -= item.balance_due
                        item.amount_paid = item.total_due + item.penalty_due
                        item.is_paid = True
                        item.paid_date = repayment.payment_date
                    else:
                        item.amount_paid += remaining
                        remaining = 0
                    item.save()

                # Close loan if fully repaid
                if loan.outstanding_balance <= Decimal('0'):
                    loan.status = LoanApplication.STATUS_CLOSED
                    loan.save()
                    messages.success(request, "Loan fully repaid and closed.")
                else:
                    messages.success(request,
                        f"UGX {repayment.amount:,.0f} recorded. "
                        f"Outstanding: UGX {loan.outstanding_balance:,.0f}")

                log_action(request.user, 'repayment', repayment,
                           after={'amount': str(repayment.amount)})
                return redirect('loans:detail', pk=loan_pk)
    else:
        form = RepaymentForm(loan=loan)

    return render(request, 'repayments/repayment_form.html', {'form': form, 'loan': loan})


@login_required
def waiver_create(request, loan_pk):
    if not (request.user.is_branch_manager or request.user.is_md or request.user.is_sys_admin):
        messages.error(request, "Only Branch Manager or MD can waive penalties.")
        return redirect('loans:detail', pk=loan_pk)
    loan = get_object_or_404(LoanApplication, pk=loan_pk)
    if request.method == 'POST':
        form = WaiverForm(request.POST, loan=loan)
        if form.is_valid():
            waiver = form.save(commit=False)
            waiver.loan = loan
            waiver.approved_by = request.user
            waiver.save()
            # Zero the penalty on the schedule item
            item = waiver.schedule_item
            item.penalty_due = max(Decimal('0'), item.penalty_due - waiver.waived_amount)
            item.save()
            log_action(request.user, 'waiver', waiver,
                       after={'amount': str(waiver.waived_amount)})
            messages.success(request, f"Penalty of UGX {waiver.waived_amount:,.0f} waived.")
            return redirect('loans:detail', pk=loan_pk)
    else:
        form = WaiverForm(loan=loan)
    return render(request, 'repayments/waiver_form.html', {'form': form, 'loan': loan})


@login_required
def restructure_create(request, loan_pk):
    if not (request.user.is_md or request.user.is_sys_admin):
        messages.error(request, "Only MD can restructure loans.")
        return redirect('loans:detail', pk=loan_pk)
    loan = get_object_or_404(LoanApplication, pk=loan_pk)
    if request.method == 'POST':
        form = RestructureForm(request.POST, loan=loan)
        if form.is_valid():
            with transaction.atomic():
                restructure = form.save(commit=False)
                restructure.loan = loan
                restructure.old_period_months = loan.approved_period_months
                restructure.approved_by = request.user
                restructure.save()
                loan.approved_period_months = restructure.new_period_months
                loan.save()
                loan.compute_schedule()
                messages.success(request, "Loan restructured. New schedule generated.")
                return redirect('loans:detail', pk=loan_pk)
    else:
        form = RestructureForm(loan=loan)
    return render(request, 'repayments/restructure_form.html', {'form': form, 'loan': loan})
