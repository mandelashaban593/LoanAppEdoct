from django import forms
from .models import Customer, Guarantor, Collateral, CustomerDocument


class CustomerForm(forms.ModelForm):
    class Meta:
        model  = Customer
        exclude = ['branch', 'created_by', 'created_at', 'updated_at',
                   'is_blacklisted', 'blacklist_reason', 'blacklisted_by', 'blacklisted_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'physical_address': forms.Textarea(attrs={'rows': 2}),
            'monthly_income': forms.NumberInput(attrs={'step': '1000'}),
            'other_income':   forms.NumberInput(attrs={'step': '1000'}),
            'monthly_expenses': forms.NumberInput(attrs={'step': '1000'}),
            'existing_loans':   forms.NumberInput(attrs={'step': '1000'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')

    def clean_nin(self):
        nin = self.cleaned_data.get('nin', '').strip().upper()
        if len(nin) < 14:
            raise forms.ValidationError("NIN must be at least 14 characters.")
        return nin

    def clean_primary_phone(self):
        phone = self.cleaned_data.get('primary_phone', '').strip()
        if not phone.startswith(('+256', '0256', '07', '03')):
            raise forms.ValidationError("Enter a valid Uganda phone number.")
        return phone


class GuarantorForm(forms.ModelForm):
    class Meta:
        model  = Guarantor
        exclude = ['customer', 'created_at']
        widgets = {'id_copy': forms.FileInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')


class CollateralForm(forms.ModelForm):
    class Meta:
        model  = Collateral
        exclude = ['customer', 'verified_by', 'created_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'market_value': forms.NumberInput(attrs={'step': '100000'}),
            'forced_sale_value': forms.NumberInput(attrs={'step': '100000'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')


class DocumentForm(forms.ModelForm):
    class Meta:
        model  = CustomerDocument
        fields = ['doc_type', 'file', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')
