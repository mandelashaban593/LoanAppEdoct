from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Branch(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    district = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_head_office = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Branches'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class User(AbstractUser):
    ROLE_FIELD_OFFICER    = 'field_officer'
    ROLE_LOAN_OFFICER     = 'loan_officer'
    ROLE_BRANCH_MANAGER   = 'branch_manager'
    ROLE_FINANCE_OFFICER  = 'finance_officer'
    ROLE_MD               = 'managing_director'
    ROLE_ADMIN            = 'admin'
    ROLE_AUDITOR          = 'auditor'

    ROLE_CHOICES = [
        (ROLE_FIELD_OFFICER,   'Field Officer'),
        (ROLE_LOAN_OFFICER,    'Loan Officer'),
        (ROLE_BRANCH_MANAGER,  'Branch Manager'),
        (ROLE_FINANCE_OFFICER, 'Finance Officer'),
        (ROLE_MD,              'Managing Director'),
        (ROLE_ADMIN,           'System Administrator'),
        (ROLE_AUDITOR,         'Internal Auditor'),
    ]

    role   = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_FIELD_OFFICER)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='users')
    phone  = models.CharField(max_length=20, blank=True)
    must_change_password = models.BooleanField(default=True)
    last_active = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_at = models.DateTimeField(null=True, blank=True)

    # Role helpers
    @property
    def is_field_officer(self):   return self.role == self.ROLE_FIELD_OFFICER
    @property
    def is_loan_officer(self):    return self.role == self.ROLE_LOAN_OFFICER
    @property
    def is_branch_manager(self):  return self.role == self.ROLE_BRANCH_MANAGER
    @property
    def is_finance_officer(self): return self.role == self.ROLE_FINANCE_OFFICER
    @property
    def is_md(self):              return self.role == self.ROLE_MD
    @property
    def is_sys_admin(self):       return self.role == self.ROLE_ADMIN
    @property
    def is_auditor(self):         return self.role == self.ROLE_AUDITOR
    @property
    def is_read_only(self):       return self.role == self.ROLE_AUDITOR
    @property
    def can_approve(self):
        return self.role in [self.ROLE_LOAN_OFFICER, self.ROLE_BRANCH_MANAGER,
                             self.ROLE_MD, self.ROLE_ADMIN]
    @property
    def can_disburse(self):
        return self.role in [self.ROLE_FINANCE_OFFICER, self.ROLE_MD, self.ROLE_ADMIN]
    @property
    def sees_all_branches(self):
        return self.role in [self.ROLE_MD, self.ROLE_ADMIN, self.ROLE_AUDITOR]

    @property
    def is_account_locked(self):
        return self.locked_at is not None

    def record_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_at = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'locked_at'])

    def reset_login_attempts(self):
        self.failed_login_attempts = 0
        self.locked_at = None
        self.last_active = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'locked_at', 'last_active'])

    def get_role_display_badge(self):
        colors = {
            self.ROLE_FIELD_OFFICER:   'badge-secondary',
            self.ROLE_LOAN_OFFICER:    'badge-primary',
            self.ROLE_BRANCH_MANAGER:  'badge-info',
            self.ROLE_FINANCE_OFFICER: 'badge-warning',
            self.ROLE_MD:              'badge-danger',
            self.ROLE_ADMIN:           'badge-dark',
            self.ROLE_AUDITOR:         'badge-light',
        }
        return colors.get(self.role, 'badge-secondary')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
