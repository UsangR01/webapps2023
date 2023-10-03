from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message

    @staticmethod
    def send_notification(recipient, alert):
        notification = Notification.objects.create(recipient=recipient, message=alert)
        return notification

    class Meta:
        ordering = ['-timestamp']
