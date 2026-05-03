# apps/repayments/forms.py
from django import forms
from .models import Repayment, PenaltyWaiver, LoanRestructure
from apps.loans.models import RepaymentSchedule


class RepaymentForm(forms.ModelForm):
    class Meta:
        model  = Repayment
        fields = ['amount', 'channel', 'reference', 'payment_date', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '1000', 'min': '1000'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, loan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loan = loan
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.loan and amount and amount > self.loan.outstanding_balance:
            # Allow overpayment — handled in view
            pass
        return amount


class WaiverForm(forms.ModelForm):
    class Meta:
        model  = PenaltyWaiver
        fields = ['schedule_item', 'waived_amount', 'reason']
        widgets = {'reason': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, loan=None, **kwargs):
        super().__init__(*args, **kwargs)
        if loan:
            self.fields['schedule_item'].queryset = RepaymentSchedule.objects.filter(
                loan=loan, penalty_due__gt=0)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')


class RestructureForm(forms.ModelForm):
    class Meta:
        model  = LoanRestructure
        fields = ['new_period_months', 'reason']
        widgets = {'reason': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, loan=None, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')
