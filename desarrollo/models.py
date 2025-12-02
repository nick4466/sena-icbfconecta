from django.db import models
from core.models import Nino
from planeaciones.models import Planeacion
from django.db.models.signals import post_save, post_delete
from django.core.validators import MinValueValidator, MaxValueValidator

class DesarrolloNino(models.Model):
    nino = models.ForeignKey(Nino, on_delete=models.CASCADE, related_name='desarrollos')
    fecha_fin_mes = models.DateField()
    
    # --- 2. Indicadores Cualitativos del Mes (Automáticos) ---
    logro_mes = models.CharField(
        max_length=20,
        choices=[('Alto', 'Alto'), ('Adecuado', 'Adecuado'), ('En Proceso', 'En Proceso')],
        verbose_name="Logro General del Mes",
        null=True, blank=True,
        help_text="Categoría cualitativa basada en la frecuencia de valoraciones diarias."
    )
    tendencia_valoracion = models.CharField(
        max_length=20,  # Aumentado para permitir 'Sin datos previos'
        choices=[('Avanza', 'Avanza'), ('Retrocede', 'Retrocede'), ('Se Mantiene', 'Se Mantiene'), ('Sin datos previos', 'Sin datos previos')],
        verbose_name="Tendencia de Valoración",
        null=True, blank=True,
        help_text="Comparación con el promedio del mes anterior."
    )
    participacion_frecuente = models.CharField(
        max_length=50, verbose_name="Participación Más Frecuente", null=True, blank=True
    )
    porcentaje_asistencia = models.PositiveSmallIntegerField(
        verbose_name="Porcentaje de Asistencia Mensual",
        null=True, blank=True,
        help_text="Porcentaje de días presentes sobre los días hábiles del mes."
    )
    comportamiento_frecuente = models.CharField(
        max_length=50, verbose_name="Comportamiento Más Frecuente", null=True, blank=True
    )

    # --- 3. Evaluación por Áreas del Desarrollo (Automática) ---
    evaluacion_cognitiva = models.TextField(verbose_name="Evaluación Cognitiva", null=True, blank=True)
    evaluacion_comunicativa = models.TextField(verbose_name="Evaluación Comunicativa / Lenguaje", null=True, blank=True)
    evaluacion_socio_afectiva = models.TextField(verbose_name="Evaluación Socio-afectiva", null=True, blank=True)
    evaluacion_corporal = models.TextField(verbose_name="Evaluación Corporal / Motricidad", null=True, blank=True)
    evaluacion_autonomia = models.TextField(verbose_name="Evaluación Autonomía", null=True, blank=True)

    # --- 4. Fortalezas del Mes (Automática) ---
    fortalezas_mes = models.TextField(
        verbose_name="Fortalezas del Mes",
        null=True, blank=True,
        help_text="Lista generada automáticamente de aspectos positivos."
    )

    # --- 5. Aspectos por Mejorar (Automáticos) ---
    aspectos_a_mejorar = models.TextField(
        verbose_name="Aspectos por Mejorar",
        null=True, blank=True,
        help_text="Lista generada automáticamente de áreas de oportunidad."
    )

    # --- 6. Alertas del Mes (Automáticas) ---
    alertas_mes = models.TextField(
        verbose_name="Alertas del Mes",
        null=True, blank=True,
        help_text="Alertas automáticas sobre inasistencias, valoraciones bajas o novedades."
    )

    # --- 7. Conclusión General (Automática) ---
    conclusion_general = models.TextField(
        verbose_name="Conclusión General del Desarrollo",
        null=True, blank=True,
        help_text="Resumen automático del progreso y estado general del niño en el mes."
    )

    # --- 8. Campos Manuales (Opcionales) ---
    observaciones_adicionales = models.TextField(
        verbose_name="Observaciones Adicionales del Educador",
        blank=True, null=True,
        help_text="Espacio para notas o comentarios manuales del educador."
    )
    recomendaciones_personales = models.TextField(
        verbose_name="Recomendaciones Personales",
        blank=True, null=True,
        help_text="Recomendaciones específicas para la familia o el seguimiento."
    )

    def __str__(self):
        return f"Desarrollo de {self.nino.nombres} para {self.fecha_fin_mes.strftime('%B %Y')}"

    class Meta:
        verbose_name = "Desarrollo del Niño"
        verbose_name_plural = "Desarrollos de los Niños"
        ordering = ['-fecha_fin_mes', 'nino']
        unique_together = ('nino', 'fecha_fin_mes')

    def save(self, *args, **kwargs):
        # El generador se ejecuta solo si no es una actualización desde el generador mismo
        run_generator = kwargs.pop('run_generator', True)
        super().save(*args, **kwargs)
        if run_generator:
            from .services import GeneradorEvaluacionMensual
            GeneradorEvaluacionMensual(self).run()
    
    def get_participacion_frecuente_display(self):
        # Mapea los valores calculados a textos legibles
        mapping = {
            'Alta': 'Participativo',
            'Media': 'Colaborativo',
            'Baja': 'Otro comportamiento'
        }
        return mapping.get(self.participacion_frecuente, self.participacion_frecuente)

    def get_comportamiento_frecuente_display(self):
        # Choices locales para mostrar el texto legible
        choices = {
            'participativo': 'Participativo',
            'aislado': 'Aislado',
            'impulsivo': 'Impulsivo',
            'inquieto': 'Inquieto',
            'tranquilo': 'Tranquilo',
            'colaborativo': 'Colaborativo',
        }
        return choices.get(self.comportamiento_frecuente, self.comportamiento_frecuente)

    def generar_evaluacion_por_dimensiones(self):
        # Obtiene los seguimientos del mes
        from .models import SeguimientoDiario, EvaluacionDimension
        seguimientos = SeguimientoDiario.objects.filter(
            nino=self.nino,
            fecha__month=self.fecha_fin_mes.month,
            fecha__year=self.fecha_fin_mes.year
        )
        # Dimensiones a considerar
        dimensiones = {
            'evaluacion_cognitiva': 'Cognitiva',
            'evaluacion_comunicativa': 'Comunicativa / Lenguaje',
            'evaluacion_socio_afectiva': 'Socio-afectiva',
            'evaluacion_corporal': 'Corporal / Motricidad',
        }
        # Inicializa los textos
        for campo, nombre in dimensiones.items():
            setattr(self, campo, '')
        # Procesa cada dimensión
        for campo, nombre in dimensiones.items():
            # Busca evaluaciones de esa dimensión en los seguimientos
            textos = []
            for seguimiento in seguimientos:
                for ev in seguimiento.evaluaciones_dimension.all():
                    if nombre.lower() in ev.dimension.nombre.lower():
                        if ev.desempeno == 'alto':
                            textos.append(f"Desempeño alto en {nombre}.")
                        elif ev.desempeno == 'adecuado':
                            textos.append(f"Desempeño adecuado en {nombre}.")
                        elif ev.desempeno == 'proceso':
                            textos.append(f"En proceso de mejora en {nombre}.")
                        elif ev.desempeno == 'bajo':
                            textos.append(f"Desempeño bajo en {nombre}.")
                        if ev.observacion:
                            textos.append(ev.observacion)
            # Genera el texto final para la dimensión
            if textos:
                texto_final = '\n'.join(textos)
            else:
                texto_final = f"No hay información suficiente para evaluar la dimensión {nombre}."
            setattr(self, campo, texto_final)
        self.save(run_generator=False)


# ------------------------
# 💡 SEGUIMIENTO DIARIO (Existente)
# ------------------------
class SeguimientoDiario(models.Model):
    nino = models.ForeignKey(Nino, on_delete=models.CASCADE, related_name='seguimientos_diarios')
    planeacion = models.ForeignKey(Planeacion, on_delete=models.CASCADE, related_name='seguimientos_diarios')
    fecha = models.DateField()

    # --- Opciones para los campos de selección ---
    COMPORTAMIENTO_CHOICES = [
        ('participativo', 'Participativo'),
        ('aislado', 'Aislado'),
        ('impulsivo', 'Impulsivo'),
        ('inquieto', 'Inquieto'),
        ('tranquilo', 'Tranquilo'),
        ('colaborativo', 'Colaborativo'),
    ]
    ESTADO_EMOCIONAL_CHOICES = [
        ('alegre', 'Alegre'),
        ('tranquilo', 'Tranquilo'),
        ('curioso', 'Curioso'),
        ('motivado', 'Motivado'),
        ('carinoso', 'Cariñoso'),
        ('cansado', 'Cansado'),
        ('triste', 'Triste'),
        ('ansioso', 'Ansioso'),
        ('frustrado', 'Frustrado'),
        ('enojado', 'Enojado / Irritado'),
        ('timido', 'Tímido / Inseguro'),
        ('aislado_emocional', 'Aislado (poco participativo)'),
    ]

    # Campos de seguimiento
    comportamiento_general = models.CharField(
        max_length=20, choices=COMPORTAMIENTO_CHOICES,
        verbose_name="Comportamiento general del niño", null=True, blank=True
    )
    estado_emocional = models.CharField(
        max_length=20, choices=ESTADO_EMOCIONAL_CHOICES,
        verbose_name="Estado emocional del niño", null=True, blank=True
    )
    observaciones = models.TextField(
        verbose_name="Observaciones del educador",
        blank=True, null=True
    )
    observacion_relevante = models.BooleanField(
        default=False,
        blank=True,
        verbose_name="¿Esta observación es relevante para el desarrollo del niño?",
        help_text="Marcar si la observación debe ser considerada en los informes de desarrollo."
    )
    valoracion = models.PositiveSmallIntegerField(
        verbose_name="Valoración del día",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Calificación de 1 a 5 estrellas."
    )

    class Meta:
        verbose_name = "Seguimiento Diario"
        verbose_name_plural = "Seguimientos Diarios"
        unique_together = ('nino', 'fecha') # Asegura un solo seguimiento por niño y día
        ordering = ['-fecha', 'nino']

    def get_full_name(self):
        """Devuelve el nombre completo del niño."""
        return self.nino.get_full_name() if self.nino else "Niño no asignado"

    def valoracion_restante(self):
        """Calcula el número de estrellas restantes para la valoración."""
        valoracion_actual = self.valoracion or 0
        return 5 - valoracion_actual


class EvaluacionDimension(models.Model):
    """
    Almacena la evaluación de una dimensión específica dentro de un seguimiento diario.
    """
    DESEMPENO_CHOICES = [
        ('alto', 'Alto'),
        ('adecuado', 'Adecuado'),
        ('proceso', 'En Proceso'),
        ('bajo', 'Bajo'),
    ]

    seguimiento = models.ForeignKey(SeguimientoDiario, on_delete=models.CASCADE, related_name='evaluaciones_dimension')
    dimension = models.ForeignKey('planeaciones.Dimension', on_delete=models.CASCADE)
    desempeno = models.CharField(max_length=10, choices=DESEMPENO_CHOICES)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('seguimiento', 'dimension')