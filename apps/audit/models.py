from django.db import models
from apps.accounts.models import User


class AuditLog(models.Model):
    ACTION_LOGIN    = 'login'
    ACTION_LOGOUT   = 'logout'
    ACTION_CREATE   = 'create'
    ACTION_UPDATE   = 'update'
    ACTION_DELETE   = 'delete'
    ACTION_APPROVE  = 'approve'
    ACTION_REJECT   = 'reject'
    ACTION_DISBURSE = 'disburse'
    ACTION_REPAY    = 'repayment'
    ACTION_WAIVE    = 'waiver'
    ACTION_EXPORT   = 'export'
    ACTION_CHOICES  = [
        (ACTION_LOGIN,   'Login'),
        (ACTION_LOGOUT,  'Logout'),
        (ACTION_CREATE,  'Create'),
        (ACTION_UPDATE,  'Update'),
        (ACTION_DELETE,  'Delete Attempt'),
        (ACTION_APPROVE, 'Approve'),
        (ACTION_REJECT,  'Reject'),
        (ACTION_DISBURSE,'Disburse'),
        (ACTION_REPAY,   'Repayment Recorded'),
        (ACTION_WAIVE,   'Penalty Waiver'),
        (ACTION_EXPORT,  'Export / Report'),
    ]

    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name  = models.CharField(max_length=100, blank=True)
    object_id   = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=300, blank=True)
    before_data = models.JSONField(null=True, blank=True)
    after_data  = models.JSONField(null=True, blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.CharField(max_length=300, blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes  = [models.Index(fields=['user','timestamp']),
                    models.Index(fields=['model_name','object_id'])]

    def __str__(self):
        return f"{self.user} — {self.get_action_display()} — {self.timestamp:%Y-%m-%d %H:%M}"


# ── notifications/models.py ──────────────────────────────────────────────────
