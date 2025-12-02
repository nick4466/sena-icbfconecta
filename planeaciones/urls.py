# planeaciones/urls.py
from django.urls import path
from . import views

app_name = 'planeaciones'

urlpatterns = [
    path('', views.lista_planeaciones, name='lista_planeaciones'),
    path('registrar/', views.registrar_planeacion, name='registrar_planeacion'),
    path('editar/<int:id>/', views.editar_planeacion, name='editar_planeacion'),
    path('eliminar/<int:id>/', views.eliminar_planeacion, name='eliminar_planeacion'),
    path('detalle/<int:id>/', views.detalle_planeacion, name='detalle_planeacion'),
    path('eliminar-masivo/', views.eliminar_masivo, name='eliminar_masivo'),

    # --- REPORTES PDF ---
    path('reporte/', views.reporte_menu, name='reporte_menu'),
    path('reporte/planeacion/<int:id>/', views.reporte_planeacion_pdf, name='reporte_individual_pdf'),
    path('reporte/todas/', views.reporte_todas_pdf, name='reporte_todas_pdf'),
    path('reporte/mes/', views.reporte_mes_pdf, name='reporte_mes_pdf'),

]