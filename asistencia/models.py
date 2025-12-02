from django.db import models
from core.models import Nino

class Asistencia(models.Model):
    nino = models.ForeignKey(Nino, on_delete=models.CASCADE)
    fecha = models.DateField()
    estado = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nino} - {self.fecha} ({self.estado})"
