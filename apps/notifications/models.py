from django.db import models
from apps.accounts.models import User


class Notification(models.Model):
    TYPE_INFO    = 'info'
    TYPE_SUCCESS = 'success'
    TYPE_WARNING = 'warning'
    TYPE_DANGER  = 'danger'
    TYPE_CHOICES = [(TYPE_INFO,'Info'),(TYPE_SUCCESS,'Success'),
                    (TYPE_WARNING,'Warning'),(TYPE_DANGER,'Alert')]

    recipient   = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='notifications')
    title       = models.CharField(max_length=200)
    message     = models.TextField()
    notif_type  = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_INFO)
    link        = models.CharField(max_length=300, blank=True)
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"→ {self.recipient.username}: {self.title}"


def notify(users, title, message, notif_type=Notification.TYPE_INFO, link=''):
    """Helper: create notifications for one or a list of users."""
    if not isinstance(users, (list, tuple)):
        users = [users]
    Notification.objects.bulk_create([
        Notification(recipient=u, title=title, message=message,
                     notif_type=notif_type, link=link)
        for u in users if u
    ])
