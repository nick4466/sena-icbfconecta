from django.urls import path
from . import views

urlpatterns = [
    path('', views.asistencia_form, name='asistencia_form'),
    path('historial/<int:nino_id>/', views.historial_asistencia, name='historial_asistencia'),
    path('historial/<int:nino_id>/pdf/', views.historial_asistencia_pdf, name='historial_pdf'),
    path('crear-novedad-desde-asistencia/', views.crear_novedad_desde_asistencia, name='crear_novedad_desde_asistencia'),
]


