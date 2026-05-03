# apps/customers/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Customer, CustomerDocument, Guarantor, Collateral
from .forms import CustomerForm, GuarantorForm, CollateralForm, DocumentForm
from apps.audit.utils import log_action


def branch_filter(user, qs):
    if user.sees_all_branches:
        return qs
    return qs.filter(branch=user.branch)


@login_required
def customer_list(request):
    search = request.GET.get('q', '')
    qs = branch_filter(request.user, Customer.objects.all())
    if search:
        qs = qs.filter(
            Q(full_name__icontains=search) |
            Q(nin__icontains=search) |
            Q(primary_phone__icontains=search))
    return render(request, 'customers/customer_list.html', {
        'customers': qs[:200], 'search': search,
        'total': qs.count(),
    })


@login_required
def customer_create(request):
    if request.user.is_auditor:
        messages.error(request, "Auditors cannot create records.")
        return redirect('customers:list')
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            customer = form.save(commit=False)
            # Duplicate NIN check
            if Customer.objects.filter(nin=customer.nin).exists():
                form.add_error('nin', 'A customer with this NIN already exists.')
            # Duplicate phone check
            elif Customer.objects.filter(primary_phone=customer.primary_phone).exists():
                form.add_error('primary_phone', 'This phone number is already registered.')
            else:
                customer.created_by = request.user
                customer.branch = request.user.branch
                customer.save()
                log_action(request.user, 'create', customer)
                messages.success(request, f"Customer {customer.full_name} created.")
                return redirect('customers:detail', pk=customer.pk)
    else:
        form = CustomerForm(user=request.user)
    return render(request, 'customers/customer_form.html', {'form': form, 'action': 'Add'})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if not request.user.sees_all_branches and customer.branch != request.user.branch:
        messages.error(request, "Access denied.")
        return redirect('customers:list')
    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'loans': customer.loan_applications.select_related('product').order_by('-created_at'),
        'guarantors': customer.guarantors.all(),
        'collaterals': customer.collaterals.all(),
        'documents': customer.documents.all(),
    })


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.user.is_auditor:
        messages.error(request, "Auditors cannot edit records.")
        return redirect('customers:detail', pk=pk)
    before = {'full_name': customer.full_name, 'nin': customer.nin}
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer, user=request.user)
        if form.is_valid():
            updated = form.save()
            log_action(request.user, 'update', updated, before)
            messages.success(request, "Customer record updated.")
            return redirect('customers:detail', pk=pk)
    else:
        form = CustomerForm(instance=customer, user=request.user)
    return render(request, 'customers/customer_form.html', {
        'form': form, 'customer': customer, 'action': 'Edit',
    })


@login_required
def customer_blacklist(request, pk):
    if not (request.user.is_md or request.user.is_sys_admin):
        messages.error(request, "Only MD or Admin can blacklist customers.")
        return redirect('customers:detail', pk=pk)
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "A reason is required.")
            return redirect('customers:detail', pk=pk)
        customer.is_blacklisted = True
        customer.blacklist_reason = reason
        customer.blacklisted_by = request.user
        customer.blacklisted_at = timezone.now()
        customer.save()
        log_action(request.user, 'update', customer, after={'blacklisted': True, 'reason': reason})
        messages.warning(request, f"{customer.full_name} has been blacklisted.")
    return redirect('customers:detail', pk=pk)
