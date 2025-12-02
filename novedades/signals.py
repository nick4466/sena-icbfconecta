from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Novedad
from notifications.models import Notification

@receiver(post_save, sender=Novedad)
def crear_notificacion(sender, instance, created, **kwargs):
    if created:
        prioridad = instance.get_prioridad()  # usar el método, no un campo
        level = "info"
        if prioridad >= 5:
            level = "grave"
        elif prioridad >= 3:
            level = "warning"

        Notification.objects.create(
            title=f"Novedad registrada: {instance.nino}",
            message=instance.descripcion,
            level=level,
            recipient=instance.usuario,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
        )
