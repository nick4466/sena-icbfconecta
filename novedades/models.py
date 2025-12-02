from django.db import models
from core.models import Nino  # Ajusta si el modelo Niño está en otra app
from django.contrib.auth import get_user_model

User = get_user_model()
class Novedad(models.Model):    
    nino = models.ForeignKey(Nino, on_delete=models.CASCADE)
    docente = models.CharField(max_length=100)
    fecha = models.DateField()
    clase = models.CharField(max_length=100)
    descripcion = models.TextField()
    causa = models.CharField(max_length=255, blank=True)
    disposicion = models.TextField(blank=True)
    acuerdos = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # 🔔 quién creó la novedad

    archivo_pdf = models.FileField(upload_to='novedades_pdfs/', blank=True, null=True)

    TIPOS_NOVEDAD = [
        ('a', 'Cambios en los estados de salud'),
        ('b', 'Cambios en el estado emocional'),
        ('c', 'Razones de inasistencia y llegadas tarde'),
        ('d', 'Inapetencia'),
        ('e', 'Cambios de medicamentos'),
        ('f', 'Inasistencia de medicamentos'),
        ('g', 'Sin registro civil'),
        ('h', 'Sin afiliación en salud'),
        ('i', 'Sin esquema de vacunación'),
        ('j', 'Otra'),
    ]

    tipo = models.CharField(max_length=1, choices=TIPOS_NOVEDAD, verbose_name="Tipo de novedad")

    def get_prioridad(self):
        prioridades = {
            'a': 5,
            'b': 4,
            'c': 3,
            'd': 2,
            'e': 4,
            'f': 3,
            'g': 2,
            'h': 3,
            'i': 4,
            'j': 1,
        }
        return prioridades.get(self.tipo, 1)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('novedades:detalle', args=[str(self.id)])

    def __str__(self):
        return f"Novedad de {self.nino.nombre} - {self.fecha}"
    
