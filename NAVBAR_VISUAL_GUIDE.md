# 🎯 Guía Visual - Navbar Unificada

## 📐 Estructura de la Navbar

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          NAVBAR UNIFICADA (sticky-top)                    ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                                            ┃
┃  [SITEMAP] ICBF Conecta  │  Dashboard  │ Niños │ Llamar Lista │ ...      ┃   [👤] [🔑] [⏻]   ┃
┃  (Click: /dashboard/madre)                                         [Nombre]        ┃
┃                                                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## 🎨 Áreas Principales

### 1️⃣ Área Izquierda (Logo)
```
┌────────────────────────────┐
│ [SITEMAP] ICBF Conecta     │  ← Logo con ícono
│                            │  ← Click redirige a dashboard
└────────────────────────────┘
```
- **Ícono**: Font Awesome - `fa-sitemap`
- **Texto**: "ICBF Conecta"
- **Función**: Logo clickeable que lleva al dashboard
- **Hover**: Efecto de opacidad y escala

### 2️⃣ Área Central (Menú Principal)
```
┌──────────────────────────────────────────────────────────────┐
│ Dashboard │ Niños │ Llamar a Lista │ Planeaciones │ Novedades │
│   📊      │  👨   │       📋      │      📅      │     ⚠️      │
└──────────────────────────────────────────────────────────────┘
```
| Enlace | Ícono | URL | Función |
|--------|-------|-----|---------|
| Dashboard | `fa-chart-line` | `madre_dashboard` | Panel principal |
| Niños | `fa-children` | `listar_ninos` | Listado de niños |
| **Llamar a Lista** ⭐ | `fa-clipboard-list` | `asistencia_form` | Registro de asistencia |
| Planeaciones | `fa-calendar-alt` | `planeaciones:lista_planeaciones` | Gestión de planeaciones |
| Novedades | `fa-exclamation-circle` | `novedades:lista_novedades` | Registro de incidentes |

### 3️⃣ Área Derecha (Menú de Usuario)
```
┌────────────────────────────────────┐
│ [Nombre Usuario]  [👤] [🔑] [⏻]     │
│                                    │
│ [Editar Perfil]  [Cambiar Pass]  [Salir] │
└────────────────────────────────────┘
```
| Elemento | Ícono | URL | Función |
|----------|-------|-----|---------|
| Nombre | - | - | Muestra nombre de usuario (truncado en mobile) |
| Editar Perfil | `fa-user-circle` | `editar_perfil` | Acceso a configuración de perfil |
| Cambiar Contraseña | `fa-key` | `cambiar_contrasena` | Cambio seguro de contraseña |
| Cerrar Sesión | `fa-sign-out-alt` | `logout` | Cierre de sesión (rojo en hover) |

---

## 🎬 Estados y Transiciones

### Estado Normal (Desktop)
```
┌─────────────────────────────────────────────────────────────┐
│ [LOGO] ICBF  │  Menu Items  │  Username  [👤] [🔑] [⏻]      │
└─────────────────────────────────────────────────────────────┘
```

### Estado Hover (Desktop)
```
┌─────────────────────────────────────────────────────────────┐
│ [LOGO]⤴ ICBF │  Dashboard↑  │  User⬆️  [👤] [🔑] [⏻]        │
│              │  (bg light)  │                               │
└─────────────────────────────────────────────────────────────┘
```
- Logo: Aumenta opacidad, ícono sube
- Menú: Fondo ligeramente transparente
- Botones: Aumentan de tamaño

### Estado Responsive (Tablet - 768px)
```
┌──────────────────────────────┐
│ [LOGO] ICBF │ Menu Items ... │ [👤] [🔑] [⏻] │
│             │ (ajustados)    │               │
└──────────────────────────────┘
```

### Estado Mobile (480px)
```
┌────────────────────────────────┐
│ [LOGO] ICBF  [👤] [🔑] [⏻]      │
├────────────────────────────────┤
│ Dashboard │ Niños │ Lista │ +   │
│ Planes   │ Noved │        │     │
└────────────────────────────────┘
```
- Nombre usuario: Oculto
- Menú: En dos filas
- Botones: Compactados

---

## 🎨 Esquema de Colores

```
Gradiente Púrpura (135°):
┌────────────────────────────────────────────┐
│ #667eea (Púrpura Claro) → #764ba2 (Oscuro) │
│                                            │
│    Inicio                          Fin     │
└────────────────────────────────────────────┘
```

### Paleta
| Elemento | Color | Código |
|----------|-------|--------|
| Fondo | Gradiente púrpura | `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` |
| Texto principal | Blanco | `#ffffff` |
| Texto secundario | Blanco con opacidad | `rgba(255, 255, 255, 0.9)` |
| Fondo hover | Blanco transparente | `rgba(255, 255, 255, 0.15)` |
| Botón logout hover | Rojo transparente | `rgba(255, 68, 68, 0.4)` |

---

## 📱 Breakpoints Responsivos

### 🖥️ Desktop (1024px+)
```
┌──────────────────────────────────────────────────────────────┐
│ [Logo]  │  All Menu Items Visible  │  User [👤] [🔑] [⏻]      │
│ 28px    │  Gap: 10px                │  Nombre: Visible         │
└──────────────────────────────────────────────────────────────┘
```
- Padding: 15px 30px
- Font size menú: 14px
- Ancho mínimo botones: Full

### 💻 Tablet (768px - 1023px)
```
┌────────────────────────────────────────────┐
│ [Logo] │ Menu Items Compact │ [👤][🔑][⏻]  │
│        │ Gap: 5px           │ Nombre: Visible
└────────────────────────────────────────────┘
```
- Padding: 12px 20px
- Font size menú: 13px
- Gap menú: 5px

### 📱 Mobile (480px - 767px)
```
┌──────────────────────────┐
│ [Logo] [👤] [🔑] [⏻]     │
├──────────────────────────┤
│ Dashboard │ Niños │ Etc  │
│ Planes   │ Novedad       │
└──────────────────────────┘
```
- Padding: 10px 15px
- Font size menú: 12px
- Ancho menú: 100%
- Nombre usuario: Oculto

### 📲 Extra Small (<480px)
```
┌────────────────────┐
│ [Logo] [👤][🔑][⏻] │
├────────────────────┤
│ Dash │ Niños │ Lis │
│ Scan │ Novel       │
└────────────────────┘
```
- Padding: 10px 15px
- Font size menú: 11px
- Ícono logo: 24px (reducido)

---

## 🔐 Variables de Contexto

La navbar espera recibir estas variables en el contexto de la vista:

```python
context = {
    'nombre_madre': f"{request.user.nombres} {request.user.apellidos}",
    # ... otras variables de contexto
}
```

### Uso en Template
```django
{{ nombre_madre }}  ← Mostrado en el área de usuario
```

---

## 🔗 Sistema de URLs

```
madre_dashboard ────────────────────→ /dashboard/madre/
listar_ninos ──────────────────────→ /ninos/
asistencia_form ───────────────────→ /asistencia/
planeaciones:lista_planeaciones ───→ /planeaciones/
novedades:lista_novedades ─────────→ /novedades/
editar_perfil ─────────────────────→ /perfil/editar/
cambiar_contrasena ────────────────→ /perfil/cambiar-contrasena/
logout ─────────────────────────────→ /logout/ (POST)
```

---

## 💾 Almacenamiento de Archivos

```
templates/
└── madre/
    ├── navbar_madre.html          ← Componente reutilizable
    ├── css/
    │   └── navbar_madre.css       ← Estilos centralizados
    ├── dashboard.html              ✅ Incluye navbar
    ├── nino_list.html              ✅ Incluye navbar
    ├── nino_form.html              ✅ Incluye navbar
    ├── nino_form_nuevo.html        ✅ Incluye navbar
    ├── gestion_ninos_list.html     ✅ Incluye navbar
    ├── desarrollo_list.html        ✅ Incluye navbar
    ├── seguimiento_diario_list.html ✅ Incluye navbar
    ├── seguimiento_diario_form.html ✅ Incluye navbar
    ├── desarrollo_form.html        ✅ Incluye navbar
    ├── editar_desarrollo.html      ✅ Incluye navbar
    ├── NAVBAR_README.md            ← Documentación
    └── (otros templates)
```

---

## 🚀 Flujo de Navegación

```
Dashboard (Inicio)
    ↓
    ├─→ Niños ──→ Listar | Agregar | Gestión | Fichas
    │
    ├─→ Llamar a Lista ──→ Registro de Asistencia
    │
    ├─→ Planeaciones ──→ Listar | Crear | Editar
    │
    ├─→ Novedades ──→ Registro de Incidentes
    │
    └─→ Usuario
        ├─→ Editar Perfil
        ├─→ Cambiar Contraseña
        └─→ Cerrar Sesión
```

---

## 📊 Estadísticas de Implementación

| Métrica | Valor |
|---------|-------|
| **Templates actualizados** | 10 |
| **Líneas de CSS** | ~300 |
| **Componentes reutilizables** | 1 |
| **URLs dinámicas** | 8 |
| **Breakpoints responsive** | 4 |
| **Ícones Font Awesome** | 11 |
| **Animaciones** | 3 (hover, scale, color) |

---

## ✨ Funcionalidades Destacadas

✅ **Logo clickeable** - Regresa al dashboard desde cualquier página
✅ **Menú sticky** - Siempre visible al hacer scroll
✅ **Botón "Llamar a Lista"** - Acceso rápido a asistencia
✅ **Menú de usuario** - Opciones de perfil y cierre seguro
✅ **Responsive completo** - Funciona en todos los dispositivos
✅ **Animaciones fluidas** - Transiciones suaves en hover
✅ **Accesibilidad** - Focus states y soporte para teclado
✅ **Z-index 1000** - Siempre sobre otros elementos
✅ **Shadow elegante** - Separación visual clara

---

*Última actualización: 28 de noviembre de 2025*
