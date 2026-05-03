from django.db import models
from apps.accounts.models import User
from apps.loans.models import LoanApplication, RepaymentSchedule


class Repayment(models.Model):
    CHANNEL_MTN    = 'mtn_momo'
    CHANNEL_AIRTEL = 'airtel_money'
    CHANNEL_BANK   = 'bank_transfer'
    CHANNEL_CASH   = 'cash'
    CHANNEL_CHOICES = [
        (CHANNEL_MTN,   'MTN Mobile Money'),
        (CHANNEL_AIRTEL,'Airtel Money'),
        (CHANNEL_BANK,  'Bank Transfer'),
        (CHANNEL_CASH,  'Cash'),
    ]

    loan            = models.ForeignKey(LoanApplication, on_delete=models.PROTECT,
                                         related_name='repayments')
    schedule_item   = models.ForeignKey(RepaymentSchedule, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='payments')
    amount          = models.DecimalField(max_digits=14, decimal_places=2)
    principal_portion = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    interest_portion  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    penalty_portion   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    channel         = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    reference       = models.CharField(max_length=100, blank=True,
                                        help_text='MTN/Airtel/Bank reference number')
    payment_date    = models.DateField()
    notes           = models.TextField(blank=True)
    recorded_by     = models.ForeignKey(User, on_delete=models.PROTECT,
                                         related_name='recorded_repayments')
    is_reversed     = models.BooleanField(default=False)
    reversed_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='reversed_repayments')
    reversal_reason = models.TextField(blank=True)
    reversed_at     = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.loan.application_number} — UGX {self.amount:,} on {self.payment_date}"


class PenaltyWaiver(models.Model):
    loan            = models.ForeignKey(LoanApplication, on_delete=models.PROTECT,
                                         related_name='waivers')
    schedule_item   = models.ForeignKey(RepaymentSchedule, on_delete=models.PROTECT)
    waived_amount   = models.DecimalField(max_digits=12, decimal_places=2)
    reason          = models.TextField()
    approved_by     = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Waiver {self.loan.application_number} — UGX {self.waived_amount:,}"


class LoanRestructure(models.Model):
    loan             = models.ForeignKey(LoanApplication, on_delete=models.PROTECT,
                                          related_name='restructures')
    old_period_months = models.PositiveSmallIntegerField()
    new_period_months = models.PositiveSmallIntegerField()
    reason           = models.TextField()
    approved_by      = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Restructure {self.loan.application_number}"
