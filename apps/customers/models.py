from django.db import models
from django.core.validators import RegexValidator
from apps.accounts.models import User, Branch


phone_validator = RegexValidator(r'^\+?256\d{9}$',
    'Enter a valid Uganda phone number e.g. +256772123456')


class Customer(models.Model):
    GENDER_MALE   = 'M'
    GENDER_FEMALE = 'F'
    GENDER_OTHER  = 'O'
    GENDER_CHOICES = [(GENDER_MALE,'Male'),(GENDER_FEMALE,'Female'),(GENDER_OTHER,'Other')]

    MARITAL_SINGLE   = 'single'
    MARITAL_MARRIED  = 'married'
    MARITAL_WIDOWED  = 'widowed'
    MARITAL_DIVORCED = 'divorced'
    MARITAL_SEP      = 'separated'
    MARITAL_CHOICES  = [(MARITAL_SINGLE,'Single'),(MARITAL_MARRIED,'Married'),
                        (MARITAL_WIDOWED,'Widowed'),(MARITAL_DIVORCED,'Divorced'),
                        (MARITAL_SEP,'Separated')]

    TYPE_SALARIED  = 'salaried'
    TYPE_TRADER    = 'trader'
    TYPE_FARMER    = 'farmer'
    TYPE_BUSINESS  = 'business'
    TYPE_BODA      = 'boda_boda'
    TYPE_INFORMAL  = 'informal'
    TYPE_CHOICES   = [(TYPE_SALARIED,'Salaried Employee'),(TYPE_TRADER,'Trader / Retailer'),
                      (TYPE_FARMER,'Farmer / Agri-business'),(TYPE_BUSINESS,'Business Owner'),
                      (TYPE_BODA,'Boda Boda Rider'),(TYPE_INFORMAL,'Other Informal Worker')]

    # Identification
    full_name           = models.CharField(max_length=200, help_text='As on National ID')
    nin                 = models.CharField(max_length=20, unique=True,
                                           help_text='National Identification Number')
    date_of_birth       = models.DateField(null=True, blank=True)
    gender              = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    marital_status      = models.CharField(max_length=20, choices=MARITAL_CHOICES, blank=True)
    dependants          = models.PositiveSmallIntegerField(default=0)

    # Contact
    primary_phone       = models.CharField(max_length=20)
    alternative_phone   = models.CharField(max_length=20, blank=True)
    email               = models.EmailField(blank=True)

    # Address
    district            = models.CharField(max_length=100)
    village_lc1         = models.CharField(max_length=200)
    physical_address    = models.TextField()
    gps_latitude        = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Next of kin
    next_of_kin_name    = models.CharField(max_length=200)
    next_of_kin_phone   = models.CharField(max_length=20)
    next_of_kin_relation = models.CharField(max_length=100, blank=True)

    # Employment / Business
    customer_type       = models.CharField(max_length=20, choices=TYPE_CHOICES)
    employer_business   = models.CharField(max_length=300)
    occupation          = models.CharField(max_length=200)
    monthly_income      = models.DecimalField(max_digits=14, decimal_places=2)
    other_income        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monthly_expenses    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    existing_loans      = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                              help_text='Monthly repayments on other loans (UGX)')

    # Banking
    bank_name           = models.CharField(max_length=200, blank=True)
    bank_account        = models.CharField(max_length=50, blank=True)
    mtn_momo_number     = models.CharField(max_length=20, blank=True)
    airtel_money_number = models.CharField(max_length=20, blank=True)

    # Photos / KYC
    photo               = models.ImageField(upload_to='customers/photos/', null=True, blank=True)
    id_front            = models.FileField(upload_to='customers/ids/', null=True, blank=True)
    id_back             = models.FileField(upload_to='customers/ids/', null=True, blank=True)

    # Blacklist
    is_blacklisted      = models.BooleanField(default=False)
    blacklist_reason    = models.TextField(blank=True)
    blacklisted_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='blacklisted_customers')
    blacklisted_at      = models.DateTimeField(null=True, blank=True)

    # Metadata
    branch              = models.ForeignKey(Branch, on_delete=models.PROTECT)
    created_by          = models.ForeignKey(User, on_delete=models.PROTECT,
                                             related_name='created_customers')
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nin']),
            models.Index(fields=['primary_phone']),
            models.Index(fields=['branch']),
        ]

    def __str__(self):
        return f"{self.full_name} — {self.nin}"

    @property
    def net_monthly_income(self):
        return (self.monthly_income + self.other_income) - self.monthly_expenses

    @property
    def total_active_loans_count(self):
        return self.loan_applications.filter(status='active').count()

    @property
    def has_active_loan(self):
        return self.loan_applications.filter(
            status__in=['approved', 'disbursed', 'active']).exists()


class CustomerDocument(models.Model):
    DOC_PAYSLIP      = 'payslip'
    DOC_BANK_STMT    = 'bank_statement'
    DOC_MOMO_STMT    = 'momo_statement'
    DOC_BIZ_LICENCE  = 'business_licence'
    DOC_OTHER        = 'other'
    DOC_CHOICES = [(DOC_PAYSLIP,'Payslip'),(DOC_BANK_STMT,'Bank Statement'),
                   (DOC_MOMO_STMT,'Mobile Money Statement'),(DOC_BIZ_LICENCE,'Business Licence'),
                   (DOC_OTHER,'Other')]

    customer     = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                     related_name='documents')
    doc_type     = models.CharField(max_length=30, choices=DOC_CHOICES)
    file         = models.FileField(upload_to='customers/documents/')
    description  = models.CharField(max_length=200, blank=True)
    uploaded_by  = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} — {self.get_doc_type_display()}"


class Guarantor(models.Model):
    customer     = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                     related_name='guarantors')
    full_name    = models.CharField(max_length=200)
    nin          = models.CharField(max_length=20)
    phone        = models.CharField(max_length=20)
    relationship = models.CharField(max_length=100)
    occupation   = models.CharField(max_length=200, blank=True)
    id_copy      = models.FileField(upload_to='guarantors/ids/', null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} (Guarantor for {self.customer.full_name})"


class Collateral(models.Model):
    TYPE_VEHICLE  = 'vehicle'
    TYPE_LAND     = 'land_title'
    TYPE_MOTO     = 'motorcycle'
    TYPE_SAVINGS  = 'savings'
    TYPE_EQUIP    = 'equipment'
    TYPE_OTHER    = 'other'
    TYPE_CHOICES  = [(TYPE_VEHICLE,'Vehicle'),(TYPE_LAND,'Land Title'),
                     (TYPE_MOTO,'Motorcycle'),(TYPE_SAVINGS,'Savings / Fixed Deposit'),
                     (TYPE_EQUIP,'Business Equipment'),(TYPE_OTHER,'Other')]

    customer        = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                        related_name='collaterals')
    collateral_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description     = models.TextField()
    market_value    = models.DecimalField(max_digits=14, decimal_places=2)
    forced_sale_value = models.DecimalField(max_digits=14, decimal_places=2)
    ownership_proof = models.FileField(upload_to='collaterals/', null=True, blank=True)
    verified_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_collateral_type_display()} — {self.customer.full_name}"
