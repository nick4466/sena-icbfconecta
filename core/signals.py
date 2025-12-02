from django.db.models.signals import post_migrate
from django.dispatch import receiver
from core.models import Rol

@receiver(post_migrate)
def crear_roles_iniciales(sender, **kwargs):
    if sender.name == 'core':
        roles = ['administrador', 'madre_comunitaria', 'padre']
        for nombre in roles:
            Rol.objects.get_or_create(nombre_rol=nombre)
