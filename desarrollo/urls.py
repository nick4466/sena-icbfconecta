from django.urls import path
from . import views

# Define un espacio de nombres para esta aplicación.
# Esto nos permite usar {% url 'desarrollo:listar_desarrollos' %} en las plantillas.
app_name = 'desarrollo'

urlpatterns = [
    # --- URLs para la Madre Comunitaria ---
    path('generar/', views.generar_evaluacion_mensual, name='generar_evaluacion'),
    path('registrar/', views.registrar_desarrollo, name='registrar_desarrollo'),  # <-- AGREGADO
    path('listado/', views.listar_desarrollos, name='listar_desarrollos'),
    path('ver/<int:id>/', views.ver_desarrollo, name='ver_desarrollo'),
    path('editar/<int:id>/', views.registrar_desarrollo, name='editar_desarrollo'),
    path('eliminar/<int:id>/', views.eliminar_desarrollo, name='eliminar_desarrollo'),
    path('eliminar-seleccionados/', views.eliminar_desarrollos_seleccionados, name='eliminar_desarrollos_seleccionados'),
    
    # --- URL para el Padre de Familia ---
    path('ver/<int:nino_id>/', views.padre_ver_desarrollo, name='padre_ver_desarrollo'),

    # --- URLs para Reportes ---
    path('reporte/resumen/<int:nino_id>/', views.reporte_resumen, name='reporte_resumen'),
    path('reporte/pdf/<int:nino_id>/', views.generar_reporte_pdf, name='generar_reporte_pdf'),
    path('certificado/<int:desarrollo_id>/', views.generar_certificado_desarrollo_pdf, name='generar_certificado_desarrollo'),

    # --- 💡 NUEVO: URLs para Seguimiento Diario ---
    path('seguimiento/registrar/', views.registrar_seguimiento_diario, name='registrar_seguimiento'),
    path('seguimiento/listado/', views.listar_seguimientos, name='listar_seguimientos'),
    path('seguimiento/editar/<int:id>/', views.editar_seguimiento_diario, name='editar_seguimiento'),
    path('seguimiento/eliminar/<int:id>/', views.eliminar_seguimiento, name='eliminar_seguimiento'),
    path('seguimiento/eliminar-lote/', views.eliminar_seguimientos_lote, name='eliminar_seguimientos_lote'),
]