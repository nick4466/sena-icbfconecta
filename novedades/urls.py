from django.urls import path
from .views import novedades_list, novedades_create, novedades_edit, novedades_delete, novedades_detail

from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'novedades'
urlpatterns = [
    path('', novedades_list, name='novedades_list'),
    path('detalle-modal/<int:novedad_id>/pdf/', views.novedades_pdf, name='novedades_pdf'),
    path('nueva/', novedades_create, name='novedades_create'),
    path('editar/<int:pk>/', novedades_edit, name='novedades_edit'),
    path('eliminar/<int:pk>/', novedades_delete, name='novedades_delete'),

    # Vista completa
    path('detalle/<int:pk>/', novedades_detail, name='novedades_detail'),
    

    # Vista reducida para modal
    path('detalle-modal/<int:novedad_id>/', views.detalle_novedad, name='detalle'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

