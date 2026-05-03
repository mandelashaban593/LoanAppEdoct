from django import forms
from .models import LoanApplication, LoanProduct
from apps.customers.models import Customer


class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model  = LoanApplication
        fields = ['customer','product','purpose','purpose_details',
                  'requested_amount','requested_period_months','repayment_channel']
        widgets = {
            'purpose_details': forms.Textarea(attrs={'rows': 3}),
            'requested_amount': forms.NumberInput(attrs={'step':'1000','min':'100000'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user and not user.sees_all_branches:
            self.fields['customer'].queryset = Customer.objects.filter(
                branch=user.branch, is_blacklisted=False)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')


class CreditAssessmentForm(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False,
                              label='Review notes')

    class Meta:
        model  = LoanApplication
        fields = ['recommended_amount','debt_to_income_ratio','credit_score','credit_passed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')


class LoanApprovalForm(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows':3}),
                              required=False, label='Approval comments')

    class Meta:
        model  = LoanApplication
        fields = ['approved_amount','approved_period_months']
        widgets = {
            'approved_amount': forms.NumberInput(attrs={'step':'1000'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')


class LoanDisbursementForm(forms.ModelForm):
    class Meta:
        model  = LoanApplication
        fields = ['disbursed_amount','disbursement_channel','disbursement_reference']
        widgets = {
            'disbursement_reference': forms.TextInput(
                attrs={'placeholder': 'MTN/Airtel/Bank transaction reference'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')
