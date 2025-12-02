"""
URL configuration for icbfconecta project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views
from core.custom_password_reset_form import CustomPasswordResetForm
from core.forms import CustomAuthForm
from django.conf import settings   
from django.conf.urls.static import static
from django.urls import path
from core.views import calendario_padres, obtener_info






urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/',
    auth_views.LoginView.as_view(template_name='login.html',authentication_form=CustomAuthForm),name='login'),

    # --- URLs para Restablecimiento de Contraseña ---
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(
             template_name="password_reset/password_reset_form.html",
             form_class=CustomPasswordResetForm
         ), 
         name="password_reset"),
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="password_reset/password_reset_done.html"), 
         name="password_reset_done"),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="password_reset/password_reset_confirm.html"), 
         name="password_reset_confirm"),
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="password_reset/password_reset_complete.html"), 
         name="password_reset_complete"),
    
    # URL de Redirección por Rol (Nuevo Punto de Entrada después del Login)
    path('dashboard/', views.role_redirect, name='role_redirect'),
    
    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/reportes/', views.admin_reportes, name='admin_reportes'),
    path('dashboard/madre/', views.madre_dashboard, name='madre_dashboard'), # Nuevo
    path('dashboard/padre/', views.padre_dashboard, name='padre_dashboard'), # Nuevo para padres

    # --- Vistas para Padres (Ahora con ID de niño) ---
    path('padre/desarrollo/<int:nino_id>/', views.padre_ver_desarrollo, name='padre_ver_desarrollo'),
    path('padre/calendario/', calendario_padres, name='calendario_padres'),
    path('padre/calendario/info/', obtener_info, name='obtener_info'),

    # --- Gestión de Perfil de Usuario ---
    path('perfil/cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/actualizar-foto/', views.actualizar_foto_perfil, name='actualizar_foto_perfil'),

    # Logout
    # next_page='home' es correcto si 'home' es la URL de aterrizaje después de cerrar sesión
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'), 

    # --- CRUD Madres ---
    path('madres/', views.listar_madres, name='listar_madres'),
    path('hogares/', views.listar_hogares, name='listar_hogares'), # <-- NUEVA RUTA
    path('madres/crear/', views.crear_madre, name='crear_madre'),
    path('madres/editar/<int:id>/', views.editar_madre, name='editar_madre'),
    path('madres/eliminar/<int:id>/', views.eliminar_madre, name='eliminar_madre'),
    path('madres/detalles/<int:id>/', views.detalles_madre_json, name='detalles_madre_json'),
    
    # --- Reportes Excel ---
    path('reportes/administradores/excel/', views.reporte_administradores_excel, name='reporte_administradores_excel'),
    path('reportes/madres/excel/', views.reporte_madres_excel, name='reporte_madres_excel'),
    path('reportes/hogares/excel/', views.reporte_hogares_excel, name='reporte_hogares_excel'),

    # --- CRUD Administradores ---
    path('administradores/', views.listar_administradores, name='listar_administradores'),
    path('administradores/crear/', views.crear_administrador, name='crear_administrador'),
    path('administradores/editar/<int:id>/', views.editar_administrador, name='editar_administrador'),
    path('administradores/eliminar/<int:id>/', views.eliminar_administrador, name='eliminar_administrador'),

    # --- CRUD Niños (Matrícula) ---
    path('buscar-padre/', views.buscar_padre_por_documento, name='buscar_padre'), # <-- NUEVA RUTA AJAX
    path('ninos/matricular/', views.matricular_nino, name='matricular_nino'),
    # --- 🆕 NUEVAS RUTAS PARA MEJORAS DE MATRÍCULA ---
    path('ninos/matricular-a-padre-existente/', views.matricular_nino_a_padre_existente, name='matricular_a_padre_existente'),
    path('ninos/cambiar-padre/', views.cambiar_padre_de_nino, name='cambiar_padre_nino'),
    path('ajax/buscar-padre-existente/', views.buscar_padre_ajax, name='buscar_padre_ajax'),
    path('ninos/', views.listar_ninos, name='listar_ninos'), # Para listar los niños del hogar
    path('ninos/<int:id>/ver/', views.ver_ficha_nino, name='ver_ficha_nino'),
    path('ninos/<int:id>/editar/', views.editar_nino, name='editar_nino'),
    path('ninos/<int:id>/eliminar/', views.eliminar_nino, name='eliminar_nino'),
    path('ninos/subir-documentos/', views.subir_documentos_nino, name='subir_documentos_nino'),
    path('gestion-ninos/', views.gestion_ninos, name='gestion_ninos'),
     path('ninos/<int:nino_id>/reporte_pdf/', views.reporte_matricula_nino_pdf, name='reporte_matricula_nino_pdf'),
     path('ninos/<int:nino_id>/certificado/', views.certificado_matricula_pdf, name='certificado_matricula_pdf'),
     path('ninos/reporte-general-hogar/', views.reporte_general_hogar_pdf, name='reporte_general_hogar'),
     path('ninos/reporte/', views.generar_reporte_ninos, name='generar_reporte_ninos'),

    # --- URLs de Desarrollo (Ahora en su propia app) ---
    path('desarrollo/', include('desarrollo.urls')),

    # --- URLs de Planeaciones ---
    # Se incluye el archivo de URLs de la app 'planeaciones'<--- tener encuenta para los botones dirigidos a planeaciones
    path('planeaciones/', include(('planeaciones.urls', 'planeaciones'), namespace='planeaciones')),

     # --- URL para cargar ciudades según la regional seleccionada (AJAX) ---
     path("ajax/cargar-ciudades/", views.cargar_ciudades, name="cargar_ciudades"),

    #-----------------------------------------------juanito---------------------------------------------#
    # --- URLs de Asistencias no borrar please ultra importarte ;D #---
    path('asistencia/', include('asistencia.urls')),

    path('novedades/', include('novedades.urls', namespace='novedades')),
    
    path('notifications/', include('notifications.urls')),

    
     # --- URLs de Correos Masivos ---
     path("correos/", include("correos.urls")),

    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)