from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    level = models.CharField(
        max_length=20,
        choices=[("grave", "Grave"), ("warning", "Warning"), ("info", "Info")],
        default="info",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    recipient = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications_received"
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications_content"
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.level})"
