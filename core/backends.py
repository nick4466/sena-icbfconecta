# core/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from .models import Usuario # Asumo que tu modelo se llama Usuario
from django.contrib.auth.backends import ModelBackend
from core.models import Usuario


class DocumentoBackend(ModelBackend):
    def authenticate(self, request, tipo_documento=None, documento=None, password=None, **kwargs):
        try:
            user = Usuario.objects.get(tipo_documento=tipo_documento, documento=documento)
        except Usuario.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None

class DocumentTypeBackend(ModelBackend):
    """
    Backend de autenticación que valida el número y el tipo de documento 
    además de la contraseña.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1. Obtener el 'tipo_documento' del formulario (request.POST)
        tipo_documento = kwargs.get('tipo_documento')

        if not tipo_documento:
            # Si no se selecciona un tipo de documento, fallar
            return None

        try:
            # 2. Buscar al usuario combinando el documento (username) y el tipo
            user = Usuario.objects.get(documento=username, tipo_documento=tipo_documento)
        except Usuario.DoesNotExist:
            # Si la combinación no existe, fallar
            return None

        # 3. Validar la contraseña
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        # Función requerida por ModelBackend
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None