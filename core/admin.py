from django.contrib import admin

from .models import Rol, Usuario, Padre, HogarComunitario, Nino, Asistencia, Planeacion, Regional, Ciudad

# Registrar modelos adicionales para poder administrar regionales y ciudades desde el admin
admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Padre)
admin.site.register(HogarComunitario)
admin.site.register(Nino)
admin.site.register(Asistencia)
admin.site.register(Planeacion)
admin.site.register(Regional)
admin.site.register(Ciudad)