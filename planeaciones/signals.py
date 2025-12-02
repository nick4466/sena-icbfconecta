from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Dimension

@receiver(post_migrate)
def crear_dimensiones_predeterminadas(sender, **kwargs):
    if sender.name != 'planeaciones':
        return

    dimensiones = [
        "Cognitiva",
        "Comunicativa",
        "Corporal",
        "Socio-afectiva",
    ]

    for nombre in dimensiones:
        Dimension.objects.get_or_create(nombre=nombre)
