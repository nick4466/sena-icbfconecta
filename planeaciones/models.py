from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Dimension(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Planeacion(models.Model):
    madre = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateField()
    nombre_experiencia = models.CharField(max_length=200)
    intencionalidad_pedagogica = models.TextField()
    materiales_utilizar = models.TextField()
    ambiente_educativo = models.TextField()
    experiencia_inicio = models.TextField()
    experiencia_pedagogica = models.TextField()
    cierre_experiencia = models.TextField()
    situaciones_presentadas = models.TextField()
    dimensiones = models.ManyToManyField(Dimension, blank=True)

    def __str__(self):
        return f"{self.nombre_experiencia} - {self.fecha}"


class Documentacion(models.Model):
    planeacion = models.ForeignKey(Planeacion, on_delete=models.CASCADE, related_name='documentos')
    imagen = models.ImageField(upload_to='documentacion/')

    def __str__(self):
        return f"Documento de {self.planeacion.nombre_experiencia}"
