from django.contrib import admin
from .models import DesarrolloNino, SeguimientoDiario

@admin.register(DesarrolloNino)
class DesarrolloNinoAdmin(admin.ModelAdmin):
    list_display = ('nino', 'fecha_fin_mes', 'tendencia_valoracion')
    list_filter = ('fecha_fin_mes', 'nino__hogar', 'tendencia_valoracion')
    search_fields = ('nino__nombres', 'nino__apellidos')

@admin.register(SeguimientoDiario)
class SeguimientoDiarioAdmin(admin.ModelAdmin):
    list_display = ('nino', 'fecha', 'planeacion', 'valoracion')
    list_filter = ('fecha', 'nino__hogar', 'valoracion')
    search_fields = ('nino__nombres', 'nino__apellidos', 'planeacion__nombre_actividad')
