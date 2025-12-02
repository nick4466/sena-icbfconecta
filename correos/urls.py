from django.urls import path
from . import views

app_name = 'correos'

urlpatterns = [
    path('enviar/', views.enviar_correos, name='enviar'),
    path('historial/', views.historial, name='historial'),
    path('historial/eliminar/<int:log_id>/', views.eliminar_log, name='eliminar_log'),
    path('historial/vaciar/', views.vaciar_historial, name='vaciar_historial'),
]
