from .models import AuditLog


def log_action(user, action, obj, before=None, after=None, ip=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=obj.__class__.__name__ if obj else '',
        object_id=str(obj.pk) if obj and hasattr(obj, 'pk') else '',
        object_repr=str(obj) if obj else '',
        before_data=before,
        after_data=after,
        ip_address=ip,
    )
