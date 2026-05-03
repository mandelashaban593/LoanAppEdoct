from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum
from django.conf import settings
from decimal import Decimal
from .models import LoanApplication, LoanProduct, ApprovalAction, RepaymentSchedule
from apps.customers.models import Customer
from apps.notifications.models import notify, Notification
from apps.audit.utils import log_action
from .forms import (LoanApplicationForm, LoanApprovalForm, LoanDisbursementForm,
                    CreditAssessmentForm)


def branch_filter(user, qs):
    """Filter queryset to user's branch unless they see all branches."""
    if user.sees_all_branches:
        return qs
    return qs.filter(branch=user.branch)


@login_required
def loan_list(request):
    status  = request.GET.get('status', '')
    search  = request.GET.get('q', '')
    qs = LoanApplication.objects.select_related(
        'customer', 'product', 'branch', 'created_by')
    qs = branch_filter(request.user, qs)

    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(
            Q(application_number__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__nin__icontains=search))

    # Stats for this user's visible loans
    stats = {
        'total':    qs.count(),
        'draft':    qs.filter(status=LoanApplication.STATUS_DRAFT).count(),
        'pending':  qs.filter(status__in=[LoanApplication.STATUS_SUBMITTED,
                                           LoanApplication.STATUS_REVIEWING]).count(),
        'active':   qs.filter(status=LoanApplication.STATUS_ACTIVE).count(),
        'overdue':  qs.filter(status=LoanApplication.STATUS_ACTIVE).count(),  # refined below
    }

    return render(request, 'loans/loan_list.html', {
        'loans': qs[:200],
        'stats': stats,
        'statuses': LoanApplication.STATUS_CHOICES,
        'current_status': status,
        'search': search,
    })


@login_required
def loan_create(request):
    if request.user.is_auditor:
        messages.error(request, "Auditors cannot create loan applications.")
        return redirect('loans:list')

    customer_id = request.GET.get('customer')
    customer = get_object_or_404(Customer, pk=customer_id) if customer_id else None

    if customer and customer.has_active_loan:
        messages.warning(request, f"{customer.full_name} already has an active loan.")

    if customer and customer.is_blacklisted:
        messages.error(request, f"{customer.full_name} is blacklisted and cannot apply.")
        return redirect('customers:detail', pk=customer_id)

    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                loan = form.save(commit=False)
                loan.created_by = request.user
                loan.branch     = request.user.branch
                loan.status     = LoanApplication.STATUS_DRAFT
                loan.save()
                log_action(request.user, 'create', loan, None,
                           {'number': loan.application_number})
                messages.success(request,
                    f"Application {loan.application_number} created as Draft.")
                return redirect('loans:detail', pk=loan.pk)
    else:
        initial = {'customer': customer} if customer else {}
        form = LoanApplicationForm(initial=initial, user=request.user)

    return render(request, 'loans/loan_form.html', {
        'form': form, 'customer': customer, 'action': 'Create',
    })


@login_required
def loan_detail(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    if not request.user.sees_all_branches and loan.branch != request.user.branch:
        messages.error(request, "You do not have access to this application.")
        return redirect('loans:list')

    actions   = loan.approval_actions.select_related('actor').all()
    schedule  = loan.schedule.all()
    repayments = loan.repayments.select_related('recorded_by').filter(is_reversed=False)
    return render(request, 'loans/loan_detail.html', {
        'loan': loan, 'actions': actions, 'schedule': schedule,
        'repayments': repayments,
        'can_edit':    loan.is_editable and not request.user.is_auditor,
        'can_submit':  loan.status == LoanApplication.STATUS_DRAFT and request.user.is_field_officer,
        'can_review':  loan.status == LoanApplication.STATUS_SUBMITTED and request.user.can_approve,
        'can_approve': loan.status == LoanApplication.STATUS_REVIEWING and request.user.can_approve,
        'can_disburse':loan.status == LoanApplication.STATUS_APPROVED and request.user.can_disburse,
        'outstanding': loan.outstanding_balance,
    })


@login_required
def loan_submit(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    if loan.status != LoanApplication.STATUS_DRAFT:
        messages.error(request, "Only Draft applications can be submitted.")
        return redirect('loans:detail', pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            loan.status = LoanApplication.STATUS_SUBMITTED
            loan.submitted_at = timezone.now()
            loan.save()
            ApprovalAction.objects.create(
                loan=loan, action=ApprovalAction.ACTION_SUBMIT,
                actor=request.user,
                comment=request.POST.get('comment', ''))

            # Notify loan officers in this branch
            from apps.accounts.models import User as AppUser
            officers = AppUser.objects.filter(
                role__in=[AppUser.ROLE_LOAN_OFFICER, AppUser.ROLE_BRANCH_MANAGER],
                branch=loan.branch, is_active=True)
            notify(list(officers),
                   f"New application: {loan.application_number}",
                   f"{loan.customer.full_name} has submitted a loan application for UGX {loan.requested_amount:,.0f}.",
                   Notification.TYPE_INFO, f"/loans/{loan.pk}/")

            log_action(request.user, 'approve', loan)
            messages.success(request, "Application submitted for review.")
    return redirect('loans:detail', pk=pk)


@login_required
def loan_review(request, pk):
    """Loan Officer starts review."""
    loan = get_object_or_404(LoanApplication, pk=pk)
    if not request.user.can_approve:
        messages.error(request, "You do not have permission to review applications.")
        return redirect('loans:detail', pk=pk)

    if request.method == 'POST':
        assessment_form = CreditAssessmentForm(request.POST, instance=loan)
        if assessment_form.is_valid():
            with transaction.atomic():
                assessment_form.save()
                loan.status = LoanApplication.STATUS_REVIEWING
                loan.loan_officer = request.user
                loan.save()
                ApprovalAction.objects.create(
                    loan=loan, action=ApprovalAction.ACTION_REVIEW,
                    actor=request.user,
                    comment=request.POST.get('comment', ''))
                messages.success(request, "Review started — application is Under Review.")
                return redirect('loans:detail', pk=pk)
    else:
        assessment_form = CreditAssessmentForm(instance=loan)

    return render(request, 'loans/loan_review.html', {
        'loan': loan, 'form': assessment_form,
    })


@login_required
def loan_approve(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    if loan.status != LoanApplication.STATUS_REVIEWING:
        messages.error(request, "Only applications Under Review can be approved.")
        return redirect('loans:detail', pk=pk)

    # MD threshold check
    md_threshold = getattr(settings, 'MD_APPROVAL_THRESHOLD', 5_000_000)
    requires_md  = (loan.requested_amount or 0) > md_threshold
    if requires_md and not request.user.is_md:
        messages.error(request,
            f"Loans above UGX {md_threshold:,.0f} require Managing Director approval.")
        return redirect('loans:detail', pk=pk)

    if request.method == 'POST':
        form = LoanApprovalForm(request.POST, instance=loan)
        if form.is_valid():
            with transaction.atomic():
                loan = form.save(commit=False)
                loan.status = LoanApplication.STATUS_APPROVED

                # Copy product interest settings to loan
                loan.interest_rate   = loan.product.interest_rate
                loan.interest_method = loan.product.interest_method
                loan.processing_fee  = (loan.approved_amount *
                                        loan.product.processing_fee_pct / 100)
                loan.insurance_fee   = loan.product.insurance_fee
                loan.save()

                ApprovalAction.objects.create(
                    loan=loan, action=ApprovalAction.ACTION_APPROVE,
                    actor=request.user,
                    comment=form.cleaned_data.get('comment', ''),
                    approved_amount=loan.approved_amount)

                # Notify finance officer
                from apps.accounts.models import User as AppUser
                finance = AppUser.objects.filter(
                    role=AppUser.ROLE_FINANCE_OFFICER,
                    branch=loan.branch, is_active=True)
                notify(list(finance),
                       f"Loan approved: {loan.application_number}",
                       f"UGX {loan.approved_amount:,.0f} approved for {loan.customer.full_name}. Ready for disbursement.",
                       Notification.TYPE_SUCCESS, f"/loans/{loan.pk}/")

                log_action(request.user, 'approve', loan,
                           after={'approved_amount': str(loan.approved_amount)})
                messages.success(request,
                    f"Loan {loan.application_number} approved for UGX {loan.approved_amount:,.0f}.")
                return redirect('loans:detail', pk=pk)
    else:
        form = LoanApprovalForm(instance=loan, initial={
            'approved_amount': loan.recommended_amount or loan.requested_amount,
            'approved_period_months': loan.requested_period_months,
        })

    return render(request, 'loans/loan_approve.html', {
        'loan': loan, 'form': form, 'requires_md': requires_md,
        'md_threshold': md_threshold,
    })


@login_required
def loan_reject(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    if not request.user.can_approve:
        messages.error(request, "You do not have permission to reject applications.")
        return redirect('loans:detail', pk=pk)

    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()
        if not comment:
            messages.error(request, "A reason is required when rejecting an application.")
            return redirect('loans:detail', pk=pk)
        with transaction.atomic():
            loan.status = LoanApplication.STATUS_REJECTED
            loan.save()
            ApprovalAction.objects.create(
                loan=loan, action=ApprovalAction.ACTION_REJECT,
                actor=request.user, comment=comment)
            log_action(request.user, 'reject', loan, after={'reason': comment})
            messages.warning(request,
                f"Application {loan.application_number} has been rejected.")
    return redirect('loans:detail', pk=pk)


@login_required
def loan_return(request, pk):
    """Return application for correction."""
    loan = get_object_or_404(LoanApplication, pk=pk)
    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()
        if not comment:
            messages.error(request, "You must provide a reason when returning an application.")
            return redirect('loans:detail', pk=pk)
        with transaction.atomic():
            loan.status = LoanApplication.STATUS_RETURNED
            loan.save()
            ApprovalAction.objects.create(
                loan=loan, action=ApprovalAction.ACTION_RETURN,
                actor=request.user, comment=comment)
            # Notify creator
            notify(loan.created_by,
                   f"Application returned: {loan.application_number}",
                   f"Your application was returned for correction. Reason: {comment}",
                   Notification.TYPE_WARNING, f"/loans/{loan.pk}/")
            messages.info(request, "Application returned for correction.")
    return redirect('loans:detail', pk=pk)


@login_required
def loan_disburse(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    if not request.user.can_disburse:
        messages.error(request, "You are not authorised to disburse loans.")
        return redirect('loans:detail', pk=pk)
    if loan.status != LoanApplication.STATUS_APPROVED:
        messages.error(request, "Only Approved loans can be disbursed.")
        return redirect('loans:detail', pk=pk)

    if request.method == 'POST':
        form = LoanDisbursementForm(request.POST, instance=loan)
        if form.is_valid():
            with transaction.atomic():
                loan = form.save(commit=False)
                loan.status        = LoanApplication.STATUS_DISBURSED
                loan.disbursed_at  = timezone.now()
                loan.disbursed_by  = request.user
                if not loan.disbursed_amount:
                    loan.disbursed_amount = loan.approved_amount
                loan.save()

                # Generate repayment schedule
                loan.status = LoanApplication.STATUS_ACTIVE
                loan.save()
                loan.compute_schedule()

                ApprovalAction.objects.create(
                    loan=loan, action=ApprovalAction.ACTION_DISBURSE,
                    actor=request.user,
                    comment=f"Disbursed via {loan.get_disbursement_channel_display()}. "
                            f"Ref: {loan.disbursement_reference}")

                log_action(request.user, 'disburse', loan,
                           after={'amount': str(loan.disbursed_amount),
                                  'reference': loan.disbursement_reference})
                messages.success(request,
                    f"UGX {loan.disbursed_amount:,.0f} disbursed. Repayment schedule generated.")
                return redirect('loans:detail', pk=pk)
    else:
        form = LoanDisbursementForm(instance=loan, initial={
            'disbursed_amount': loan.approved_amount,
        })

    return render(request, 'loans/loan_disburse.html', {'loan': loan, 'form': form})


@login_required
def loan_edit(request, pk):
    loan = get_object_or_404(LoanApplication, pk=pk)
    if not loan.is_editable:
        messages.error(request, "This application cannot be edited in its current status.")
        return redirect('loans:detail', pk=pk)
    if request.user.is_auditor:
        messages.error(request, "Auditors cannot edit applications.")
        return redirect('loans:detail', pk=pk)

    before = {'status': loan.status, 'amount': str(loan.requested_amount)}
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, instance=loan, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                updated = form.save()
                log_action(request.user, 'update', updated, before,
                           {'amount': str(updated.requested_amount)})
                messages.success(request, "Application updated.")
                return redirect('loans:detail', pk=pk)
    else:
        form = LoanApplicationForm(instance=loan, user=request.user)

    return render(request, 'loans/loan_form.html', {
        'form': form, 'loan': loan, 'action': 'Edit',
    })
