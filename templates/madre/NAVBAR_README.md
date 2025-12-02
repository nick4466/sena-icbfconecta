# Navbar Unificada - Documentación

## 📋 Descripción General

La navbar unificada es un componente reutilizable que se incluye en todos los templates del módulo de "Madre Comunitaria" para garantizar una experiencia consistente en toda la aplicación.

## 🏗️ Estructura

### Archivo Principal
- **templates/madre/navbar_madre.html** - Componente navbar (con include de CSS)

### Archivo de Estilos
- **static/css/navbar_madre.css** - Estilos centralizados de la navbar

## 🔗 Cómo Usar

Para incluir la navbar en cualquier template de madre, simplemente agrega esta línea después de `<body>`:

```django
{% include 'madre/navbar_madre.html' %}
```

### Ejemplo Completo
```django-html
{% load static %}
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Mi Página</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
{% include 'madre/navbar_madre.html' %}

<!-- Tu contenido aquí -->

</body>
</html>
```

## 📍 Componentes de la Navbar

### 1. **Logo/Marca** (header-left)
- Ícono del sitemap
- Texto "ICBF Conecta"
- Al hacer clic, redirige a `madre_dashboard`

### 2. **Menú Principal** (navbar-menu)
Contiene los siguientes enlaces:
- **Dashboard** - `/dashboard/madre/` - Vista principal
- **Niños** - `/ninos/` - Listado de niños matriculados
- **Llamar a Lista** - `/asistencia/` - Registro de asistencia
- **Planeaciones** - `/planeaciones/` - Gestión de planeaciones
- **Novedades** - `/novedades/` - Registro de novedades/incidentes

### 3. **Menú de Usuario** (user-menu)
Es un menú desplegable que se activa al pasar el cursor sobre el ícono de usuario. Contiene:
- **Nombre de la madre comunitaria**.
- Enlace para **Editar Perfil** (`/editar_perfil/`).
- Enlace para **Cambiar Contraseña** (`/cambiar_contrasena/`).
- Botón para **Cerrar Sesión** (`/logout/`).

## 🎨 Diseño

### Colores
```css
--primary-gradient-start: #667eea;     /* Púrpura claro */
--primary-gradient-end: #764ba2;       /* Púrpura oscuro */
--white: #ffffff;
--light-gray: #f5f7fa;
--dark-text: #333333;
```

### Características de Diseño
- **Gradiente**: Degradado de púrpura de 135 grados
- **Sticky**: La navbar permanece en la parte superior al desplazarse
- **Responsive**: Se adapta automáticamente a diferentes tamaños de pantalla
- **Sombra**: Sombra sutil debajo para separación visual
- **Transiciones suaves**: Animaciones en hover

## 📱 Responsive Breakpoints

### Desktop (1024px+)
- Todos los elementos visibles
- Nombre de usuario completo mostrado
- Máximo ancho de menú

### Tablet (768px - 1023px)
- Menú se ajusta a dos filas si es necesario
- Estilos comprimidos
- Nombre de usuario visible

### Mobile (480px - 767px)
- Menú en vista de 100% width
- Botones adaptados
- Nombre de usuario oculto
- Ícono del logo reducido

### Extra-Small (<480px)
- Tamaños mínimos de fuente
- Espaciado reducido
- Navegación compactada

## 🔄 Actualizar Todos los Templates

Todos los siguientes templates ya incluyen la navbar unificada:

### ✅ Templates Actualizados (10)
1. nino_list.html - Listado de niños
2. nino_form.html - Formulario de nuevo niño
3. nino_form_nuevo.html - Formulario alternativo
4. gestion_ninos_list.html - Gestión de niños
5. nino_ficha.html - Ficha del niño (sin navbar - es modal)
6. desarrollo_list.html - Listado de desarrollo
7. seguimiento_diario_list.html - Listado de seguimiento
8. seguimiento_diario_form.html - Formulario de seguimiento
9. desarrollo_form.html - Formulario de desarrollo
10. editar_desarrollo.html - Edición de desarrollo

### ⚫ Templates sin navbar (No aplica)
- reporte_general_hogar.html - Reporte (vista de impresión)
- reporte_ninos.html - Reporte de niños (vista de impresión)
- certificado_matricula.html - Certificado (vista de impresión)

## 📝 Variables de Contexto Requeridas

La navbar requiere que el contexto incluya:
- `nombre_madre` - Nombre completo de la madre comunitaria (mostrado en el menú de usuario)

Ejemplo en view:
```python
context = {
    'nombre_madre': f"{request.user.nombres} {request.user.apellidos}",
    # ... resto de variables
}
return render(request, 'template.html', context)
```

## 🔐 URLs Esperadas

La navbar utiliza las siguientes URLs via `{% url %}`:
- `madre_dashboard` - Dashboard principal
- `listar_ninos` - Listado de niños
- `asistencia_form` - Formulario de asistencia
- `planeaciones:lista_planeaciones` - Listado de planeaciones
- `novedades:lista_novedades` - Listado de novedades
- `editar_perfil` - Edición de perfil
- `cambiar_contrasena` - Cambio de contraseña
- `logout` - Cerrar sesión

Verifica que todas estas URLs estén definidas en tu `urls.py`.

## 🛠️ Personalización

### Cambiar Colores
Edita `static/css/navbar_madre.css` y modifica las variables CSS en `:root`:

```css
:root {
    --primary-gradient-start: #667eea;  /* Cambiar color 1 */
    --primary-gradient-end: #764ba2;    /* Cambiar color 2 */
}
```

### Agregar Nuevos Enlaces
Edita `templates/madre/navbar_madre.html` y agrega un `<li>` en el menú:

```django-html
<li><a href="{% url 'tu_url' %}"><i class="fas fa-icon"></i> Tu Enlace</a></li>
```

### Cambiar Ícono del Logo
Busca en `navbar_madre.html`:
```django-html
<i class="fas fa-sitemap"></i>
```
Y reemplaza `fa-sitemap` con otro ícono de Font Awesome.

## 🐛 Troubleshooting

### La navbar no aparece
1. Verifica que Font Awesome esté cargado en tu template base
2. Confirma que el archivo `navbar_madre.css` existe en la ruta correcta
3. Revisa la consola del navegador para errores de CSS

### Los estilos no se aplican
1. Limpia el caché del navegador (Ctrl+F5)
2. Verifica que `{% load static %}` esté en el template
3. Revisa que la ruta del CSS sea correcta: `{% static 'css/navbar_madre.css' %}`

### Los enlaces no funcionan
1. Verifica que las URLs estén definidas en `urls.py`
2. Comprueba que los nombres de URL sean exactos
3. Usa `python manage.py show_urls` para listar todas las URLs disponibles

## 📊 Mantenimiento

Para actualizar la navbar en el futuro:
1. Edita `templates/madre/navbar_madre.html` para cambios HTML
2. Edita `static/css/navbar_madre.css` para cambios de estilos
3. Los cambios se aplicarán automáticamente a todos los templates que incluyan la navbar

No necesitas actualizar cada template individualmente.

## 📞 Soporte

Si encuentras problemas con la navbar:
1. Verifica que `{% include 'madre/navbar_madre.html' %}` esté correctamente colocado
2. Asegúrate de que las URLs necesarias estén definidas
3. Revisa que `nombre_madre` esté en el contexto
4. Limpia caché y recarga la página

---

**Última actualización:** 28 de noviembre de 2025
**Versión:** 1.0
