from django.db import models

class ArchivoAdjunto(models.Model):
    archivo = models.FileField(upload_to='correos_adjuntos/')
    nombre_original = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.nombre_original and self.archivo:
            self.nombre_original = self.archivo.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_original


class EmailLog(models.Model):
    asunto = models.CharField(max_length=255)
    cuerpo = models.TextField()
    destinatarios = models.TextField(help_text="Correos separados por coma")
    fecha_envio = models.DateTimeField(auto_now_add=True)
    adjuntos = models.ManyToManyField(ArchivoAdjunto, blank=True)
    enviado_con_exito = models.BooleanField(default=True)
    nota_error = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asunto} — {self.fecha_envio.strftime('%Y-%m-%d %H:%M')}"
