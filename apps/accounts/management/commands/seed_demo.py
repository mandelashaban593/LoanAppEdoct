"""
python manage.py seed_demo

Creates all branches, one user per role, three loan products,
five demo customers, and two sample loan applications.
Safe to run multiple times (uses get_or_create throughout).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed the database with demo branches, users, products and customers'

    def handle(self, *args, **options):
        from apps.accounts.models import Branch, User
        from apps.customers.models import Customer
        from apps.loans.models import LoanProduct

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== LMS Demo Seed ===\n'))

        # ── 1. Branches ───────────────────────────────────────────────────────
        branches_data = [
            {'name': 'Kampala Head Office', 'code': 'KLA-HQ',
             'district': 'Kampala', 'is_head_office': True},
            {'name': 'Wakiso Branch',       'code': 'WAK-01', 'district': 'Wakiso'},
            {'name': 'Mbarara Branch',      'code': 'MBA-02', 'district': 'Mbarara'},
            {'name': 'Gulu Branch',         'code': 'GUL-03', 'district': 'Gulu'},
        ]
        branches = {}
        for bd in branches_data:
            b, created = Branch.objects.get_or_create(
                code=bd['code'],
                defaults={**bd, 'is_active': True})
            branches[bd['code']] = b
            flag = '✓ created' if created else '  exists'
            self.stdout.write(f'  Branch {flag}: {b}')

        hq = branches['KLA-HQ']

        # ── 2. Users ──────────────────────────────────────────────────────────
        users_data = [
            {'username': 'admin',      'first_name': 'System',   'last_name': 'Admin',
             'role': User.ROLE_ADMIN,           'branch': hq,             'email': 'admin@lms.ug'},
            {'username': 'md',         'first_name': 'Richard',  'last_name': 'Tumwine',
             'role': User.ROLE_MD,              'branch': hq,             'email': 'md@lms.ug'},
            {'username': 'loan.officer','first_name': 'Grace',   'last_name': 'Nakato',
             'role': User.ROLE_LOAN_OFFICER,    'branch': hq,             'email': 'grace@lms.ug'},
            {'username': 'field.officer','first_name': 'Moses',  'last_name': 'Okello',
             'role': User.ROLE_FIELD_OFFICER,   'branch': hq,             'email': 'moses@lms.ug'},
            {'username': 'branch.mgr', 'first_name': 'Harriet',  'last_name': 'Atim',
             'role': User.ROLE_BRANCH_MANAGER,  'branch': branches['WAK-01'], 'email': 'harriet@lms.ug'},
            {'username': 'finance',    'first_name': 'Joseph',   'last_name': 'Ssempala',
             'role': User.ROLE_FINANCE_OFFICER, 'branch': hq,             'email': 'joseph@lms.ug'},
            {'username': 'auditor',    'first_name': 'Agnes',    'last_name': 'Auma',
             'role': User.ROLE_AUDITOR,         'branch': hq,             'email': 'agnes@lms.ug'},
        ]
        created_users = {}
        for ud in users_data:
            u, created = User.objects.get_or_create(
                username=ud['username'],
                defaults={
                    'first_name': ud['first_name'],
                    'last_name':  ud['last_name'],
                    'email':      ud['email'],
                    'role':       ud['role'],
                    'branch':     ud['branch'],
                    'must_change_password': False,
                    'is_staff':   ud['role'] in [User.ROLE_ADMIN],
                    'is_superuser': ud['username'] == 'admin',
                })
            if created:
                u.set_password('Demo@1234')
                u.save()
            created_users[ud['username']] = u
            flag = '✓ created' if created else '  exists'
            self.stdout.write(f'  User  {flag}: {u.username} ({u.get_role_display()})')

        self.stdout.write(self.style.SUCCESS(
            '\n  All users → password: Demo@1234\n'))

        # ── 3. Loan Products ──────────────────────────────────────────────────
        products_data = [
            {
                'name': 'Personal Loan', 'code': 'PL001',
                'min_amount': Decimal('100000'), 'max_amount': Decimal('5000000'),
                'min_period_months': 1, 'max_period_months': 12,
                'repayment_frequency': LoanProduct.FREQ_MONTHLY,
                'interest_method': LoanProduct.METHOD_FLAT,
                'interest_rate': Decimal('10'),
                'processing_fee_pct': Decimal('2'),
                'insurance_fee': Decimal('20000'),
                'penalty_rate': Decimal('2'),
                'grace_period_days': 3,
                'requires_guarantor': True, 'min_guarantors': 1,
                'requires_collateral': False, 'collateral_threshold': Decimal('0'),
                'allow_early_settlement': True, 'allow_top_up': False,
            },
            {
                'name': 'Business Loan', 'code': 'BL002',
                'min_amount': Decimal('500000'), 'max_amount': Decimal('20000000'),
                'min_period_months': 1, 'max_period_months': 36,
                'repayment_frequency': LoanProduct.FREQ_MONTHLY,
                'interest_method': LoanProduct.METHOD_REDUCING,
                'interest_rate': Decimal('5'),
                'processing_fee_pct': Decimal('2'),
                'insurance_fee': Decimal('50000'),
                'penalty_rate': Decimal('2'),
                'grace_period_days': 5,
                'requires_guarantor': True, 'min_guarantors': 2,
                'requires_collateral': True, 'collateral_threshold': Decimal('5000000'),
                'allow_early_settlement': True, 'allow_top_up': True,
                'top_up_min_repayment_pct': 50,
            },
            {
                'name': 'Emergency Loan', 'code': 'EL003',
                'min_amount': Decimal('50000'), 'max_amount': Decimal('500000'),
                'min_period_months': 1, 'max_period_months': 3,
                'repayment_frequency': LoanProduct.FREQ_MONTHLY,
                'interest_method': LoanProduct.METHOD_FLAT,
                'interest_rate': Decimal('8'),
                'processing_fee_pct': Decimal('1'),
                'insurance_fee': Decimal('0'),
                'penalty_rate': Decimal('5'),
                'grace_period_days': 0,
                'requires_guarantor': False, 'min_guarantors': 0,
                'requires_collateral': False, 'collateral_threshold': Decimal('0'),
                'allow_early_settlement': True, 'allow_top_up': False,
            },
        ]
        admin_user = created_users['admin']
        for pd in products_data:
            prod, created = LoanProduct.objects.get_or_create(
                code=pd['code'],
                defaults={**pd, 'is_active': True, 'created_by': admin_user})
            flag = '✓ created' if created else '  exists'
            self.stdout.write(f'  Product {flag}: {prod.name}')

        # ── 4. Demo Customers ─────────────────────────────────────────────────
        field_officer = created_users['field.officer']
        customers_data = [
            {
                'full_name': 'John Bosco Ssemanda',
                'nin': 'CM1234567890ABCDE',
                'primary_phone': '0772123456',
                'mtn_momo_number': '0772123456',
                'district': 'Kampala',
                'village_lc1': 'Kamwokya Cell',
                'physical_address': 'Near Shell Kamwokya, green gate',
                'customer_type': Customer.TYPE_SALARIED,
                'employer_business': 'Mukwano Industries Ltd',
                'occupation': 'Accounts Clerk',
                'monthly_income': Decimal('1500000'),
                'other_income': Decimal('200000'),
                'monthly_expenses': Decimal('700000'),
                'existing_loans': Decimal('0'),
                'next_of_kin_name': 'Mary Ssemanda',
                'next_of_kin_phone': '0701000001',
                'next_of_kin_relation': 'Spouse',
            },
            {
                'full_name': 'Sarah Nakirya Namuli',
                'nin': 'CF9876543210XYZAB',
                'primary_phone': '0752345678',
                'mtn_momo_number': '0752345678',
                'district': 'Wakiso',
                'village_lc1': 'Nansana Central',
                'physical_address': 'Opp. Nansana market, blue house',
                'customer_type': Customer.TYPE_TRADER,
                'employer_business': 'Nakirya General Store',
                'occupation': 'Retail Trader',
                'monthly_income': Decimal('2200000'),
                'other_income': Decimal('300000'),
                'monthly_expenses': Decimal('900000'),
                'existing_loans': Decimal('200000'),
                'next_of_kin_name': 'Paul Namuli',
                'next_of_kin_phone': '0701000002',
                'next_of_kin_relation': 'Husband',
            },
            {
                'full_name': 'Moses Atim Okello',
                'nin': 'CM5432167890KLMNO',
                'primary_phone': '0783456789',
                'mtn_momo_number': '0783456789',
                'district': 'Gulu',
                'village_lc1': 'Pece Division',
                'physical_address': 'Pece Road, white gate opposite school',
                'customer_type': Customer.TYPE_FARMER,
                'employer_business': 'Okello Agri-Farm',
                'occupation': 'Maize & Groundnut Farmer',
                'monthly_income': Decimal('900000'),
                'other_income': Decimal('150000'),
                'monthly_expenses': Decimal('400000'),
                'existing_loans': Decimal('0'),
                'next_of_kin_name': 'Grace Okello',
                'next_of_kin_phone': '0701000003',
                'next_of_kin_relation': 'Sister',
            },
        ]
        for cd in customers_data:
            cust, created = Customer.objects.get_or_create(
                nin=cd['nin'],
                defaults={
                    **cd,
                    'branch': hq,
                    'created_by': field_officer,
                    'gender': Customer.GENDER_MALE
                        if cd['full_name'].startswith('John') or
                           cd['full_name'].startswith('Moses') else Customer.GENDER_FEMALE,
                })
            flag = '✓ created' if created else '  exists'
            self.stdout.write(f'  Customer {flag}: {cust.full_name}')

        self.stdout.write(self.style.SUCCESS('\n=== Seed complete! ==='))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  URL:      http://127.0.0.1:8000/accounts/login/')
        self.stdout.write('  Password: Demo@1234  (all users)\n')
        self.stdout.write('  admin        → System Administrator (full access)')
        self.stdout.write('  md           → Managing Director (final approver)')
        self.stdout.write('  loan.officer → Loan Officer (reviewer)')
        self.stdout.write('  field.officer→ Field Officer (application creator)')
        self.stdout.write('  branch.mgr   → Branch Manager (Wakiso)')
        self.stdout.write('  finance      → Finance Officer (disburser)')
        self.stdout.write('  auditor      → Internal Auditor (read-only)\n')
