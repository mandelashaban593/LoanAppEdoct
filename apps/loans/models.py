from django.db import models
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from apps.accounts.models import User, Branch
from apps.customers.models import Customer, Guarantor, Collateral


class LoanProduct(models.Model):
    METHOD_FLAT      = 'flat'
    METHOD_REDUCING  = 'reducing'
    METHOD_CHOICES   = [(METHOD_FLAT,'Flat Rate'),(METHOD_REDUCING,'Reducing Balance')]

    FREQ_WEEKLY   = 'weekly'
    FREQ_BIWEEKLY = 'biweekly'
    FREQ_MONTHLY  = 'monthly'
    FREQ_CHOICES  = [(FREQ_WEEKLY,'Weekly'),(FREQ_BIWEEKLY,'Bi-weekly'),(FREQ_MONTHLY,'Monthly')]

    name             = models.CharField(max_length=100)
    code             = models.CharField(max_length=20, unique=True)
    description      = models.TextField(blank=True)
    min_amount       = models.DecimalField(max_digits=14, decimal_places=2)
    max_amount       = models.DecimalField(max_digits=14, decimal_places=2)
    min_period_months = models.PositiveSmallIntegerField(default=1)
    max_period_months = models.PositiveSmallIntegerField(default=12)
    repayment_frequency = models.CharField(max_length=20, choices=FREQ_CHOICES,
                                           default=FREQ_MONTHLY)
    interest_method  = models.CharField(max_length=20, choices=METHOD_CHOICES,
                                        default=METHOD_FLAT)
    interest_rate    = models.DecimalField(max_digits=5, decimal_places=2,
                                           help_text='Monthly rate %')
    processing_fee_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                              help_text='% of loan amount')
    insurance_fee    = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                           help_text='Fixed UGX amount')
    penalty_rate     = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                           help_text='Monthly % on overdue balance')
    grace_period_days = models.PositiveSmallIntegerField(default=3)
    requires_guarantor = models.BooleanField(default=True)
    min_guarantors   = models.PositiveSmallIntegerField(default=1)
    requires_collateral = models.BooleanField(default=False)
    collateral_threshold = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    allow_early_settlement = models.BooleanField(default=True)
    allow_top_up     = models.BooleanField(default=False)
    top_up_min_repayment_pct = models.PositiveSmallIntegerField(default=50)
    is_active        = models.BooleanField(default=True)
    created_by       = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class LoanApplication(models.Model):
    # Statuses
    STATUS_DRAFT      = 'draft'
    STATUS_SUBMITTED  = 'submitted'
    STATUS_REVIEWING  = 'under_review'
    STATUS_RETURNED   = 'returned'
    STATUS_APPROVED   = 'approved'
    STATUS_REJECTED   = 'rejected'
    STATUS_DISBURSED  = 'disbursed'
    STATUS_ACTIVE     = 'active'
    STATUS_CLOSED     = 'closed'
    STATUS_WRITTEN_OFF = 'written_off'

    STATUS_CHOICES = [
        (STATUS_DRAFT,      'Draft'),
        (STATUS_SUBMITTED,  'Submitted'),
        (STATUS_REVIEWING,  'Under Review'),
        (STATUS_RETURNED,   'Returned for Correction'),
        (STATUS_APPROVED,   'Approved'),
        (STATUS_REJECTED,   'Rejected'),
        (STATUS_DISBURSED,  'Disbursed'),
        (STATUS_ACTIVE,     'Active'),
        (STATUS_CLOSED,     'Closed / Settled'),
        (STATUS_WRITTEN_OFF,'Written Off'),
    ]

    PURPOSE_CHOICES = [
        ('school_fees',      'School Fees'),
        ('business',         'Business Expansion'),
        ('emergency',        'Medical / Emergency'),
        ('house',            'House Construction / Repair'),
        ('farm_inputs',      'Farm Inputs'),
        ('asset_purchase',   'Asset Purchase'),
        ('personal',         'Personal Needs'),
        ('other',            'Other'),
    ]

    CHANNEL_MTN     = 'mtn_momo'
    CHANNEL_AIRTEL  = 'airtel_money'
    CHANNEL_BANK    = 'bank_transfer'
    CHANNEL_CASH    = 'cash'
    CHANNEL_CHOICES = [(CHANNEL_MTN,'MTN Mobile Money'),(CHANNEL_AIRTEL,'Airtel Money'),
                       (CHANNEL_BANK,'Bank Transfer'),(CHANNEL_CASH,'Cash')]

    # Application identity
    application_number = models.CharField(max_length=30, unique=True, editable=False)
    customer        = models.ForeignKey(Customer, on_delete=models.PROTECT,
                                        related_name='loan_applications')
    product         = models.ForeignKey(LoanProduct, on_delete=models.PROTECT)
    branch          = models.ForeignKey(Branch, on_delete=models.PROTECT)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                       default=STATUS_DRAFT)

    # Loan details
    purpose         = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    purpose_details = models.TextField(blank=True)
    requested_amount = models.DecimalField(max_digits=14, decimal_places=2)
    recommended_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    approved_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    requested_period_months = models.PositiveSmallIntegerField()
    approved_period_months = models.PositiveSmallIntegerField(null=True, blank=True)
    repayment_channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES,
                                         default=CHANNEL_MTN)

    # Computed at approval
    interest_rate   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    interest_method = models.CharField(max_length=20, blank=True)
    processing_fee  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_fee   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_interest  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_repayable = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Disbursement
    disbursed_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    disbursed_at     = models.DateTimeField(null=True, blank=True)
    disbursed_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='disbursed_loans')
    disbursement_reference = models.CharField(max_length=100, blank=True)
    disbursement_channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, blank=True)

    # Credit assessment
    debt_to_income_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credit_score    = models.PositiveSmallIntegerField(null=True, blank=True)
    credit_passed   = models.BooleanField(null=True, blank=True)

    # Guarantors & collateral
    guarantors      = models.ManyToManyField(Guarantor, blank=True)
    collaterals     = models.ManyToManyField(Collateral, blank=True)

    # Staff
    created_by      = models.ForeignKey(User, on_delete=models.PROTECT,
                                        related_name='created_applications')
    loan_officer    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='reviewed_applications')

    # Dates
    created_at      = models.DateTimeField(auto_now_add=True)
    submitted_at    = models.DateTimeField(null=True, blank=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['customer']),
        ]

    def save(self, *args, **kwargs):
        if not self.application_number:
            self.application_number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        year = timezone.now().year
        prefix = f"LN-{year}-"
        last = LoanApplication.objects.filter(
            application_number__startswith=prefix
        ).order_by('-application_number').first()
        if last:
            try:
                seq = int(last.application_number.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    def __str__(self):
        return f"{self.application_number} — {self.customer.full_name}"

    @property
    def is_editable(self):
        return self.status in [self.STATUS_DRAFT, self.STATUS_RETURNED]

    @property
    def outstanding_balance(self):
        paid = sum(r.amount for r in self.repayments.filter(is_reversed=False))
        return max(Decimal('0'), (self.total_repayable or Decimal('0')) - paid)

    @property
    def total_paid(self):
        return sum(r.amount for r in self.repayments.filter(is_reversed=False))

    @property
    def is_overdue(self):
        today = date.today()
        return self.schedule.filter(
            due_date__lt=today, is_paid=False).exists()

    def compute_schedule(self):
        """Generate repayment schedule and store to database."""
        self.schedule.all().delete()
        if not self.approved_amount or not self.approved_period_months:
            return
        principal = self.approved_amount
        months    = self.approved_period_months
        rate      = (self.interest_rate or Decimal('0')) / 100
        disbursed = self.disbursed_at.date() if self.disbursed_at else date.today()

        schedules = []
        if self.interest_method == LoanProduct.METHOD_FLAT:
            total_interest = principal * rate * months
            total = principal + total_interest
            instalment = (total / months).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            for i in range(1, months + 1):
                due = disbursed + relativedelta(months=i)
                # Move weekend to Monday
                while due.weekday() >= 5:
                    due += timedelta(days=1)
                schedules.append(RepaymentSchedule(
                    loan=self, instalment_number=i, due_date=due,
                    principal_due=principal / months,
                    interest_due=total_interest / months,
                    total_due=instalment))
        else:  # Reducing balance
            bal = principal
            for i in range(1, months + 1):
                interest = (bal * rate).quantize(Decimal('0.01'))
                principal_portion = (principal / months).quantize(Decimal('0.01'))
                instalment = (principal_portion + interest).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                due = disbursed + relativedelta(months=i)
                while due.weekday() >= 5:
                    due += timedelta(days=1)
                schedules.append(RepaymentSchedule(
                    loan=self, instalment_number=i, due_date=due,
                    principal_due=principal_portion,
                    interest_due=interest, total_due=instalment))
                bal -= principal_portion

        RepaymentSchedule.objects.bulk_create(schedules)
        # Update totals
        self.total_interest = sum(s.interest_due for s in schedules)
        self.total_repayable = sum(s.total_due for s in schedules)
        self.save(update_fields=['total_interest', 'total_repayable'])


class ApprovalAction(models.Model):
    ACTION_SUBMIT   = 'submit'
    ACTION_REVIEW   = 'start_review'
    ACTION_RETURN   = 'return'
    ACTION_APPROVE  = 'approve'
    ACTION_REJECT   = 'reject'
    ACTION_DISBURSE = 'disburse'
    ACTION_CHOICES  = [
        (ACTION_SUBMIT,  'Submitted'),
        (ACTION_REVIEW,  'Started Review'),
        (ACTION_RETURN,  'Returned for Correction'),
        (ACTION_APPROVE, 'Approved'),
        (ACTION_REJECT,  'Rejected'),
        (ACTION_DISBURSE,'Disbursed'),
    ]

    loan        = models.ForeignKey(LoanApplication, on_delete=models.CASCADE,
                                     related_name='approval_actions')
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor       = models.ForeignKey(User, on_delete=models.PROTECT)
    comment     = models.TextField(blank=True)
    approved_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.loan.application_number} — {self.get_action_display()} by {self.actor}"


class RepaymentSchedule(models.Model):
    loan             = models.ForeignKey(LoanApplication, on_delete=models.CASCADE,
                                          related_name='schedule')
    instalment_number = models.PositiveSmallIntegerField()
    due_date         = models.DateField()
    principal_due    = models.DecimalField(max_digits=14, decimal_places=2)
    interest_due     = models.DecimalField(max_digits=14, decimal_places=2)
    penalty_due      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_due        = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_paid          = models.BooleanField(default=False)
    paid_date        = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['instalment_number']
        unique_together = ['loan', 'instalment_number']

    def __str__(self):
        return f"{self.loan.application_number} — Inst #{self.instalment_number}"

    @property
    def balance_due(self):
        return self.total_due + self.penalty_due - self.amount_paid

    @property
    def is_overdue(self):
        return not self.is_paid and self.due_date < date.today()

    @property
    def days_overdue(self):
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0
