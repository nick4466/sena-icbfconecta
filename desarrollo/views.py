from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from .models import DesarrolloNino, SeguimientoDiario, EvaluacionDimension
from planeaciones.models import Planeacion as PlaneacionModel
from novedades.models import Novedad
from core.models import Nino, HogarComunitario, Padre, MadreComunitaria
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.conf import settings
import os
from django.core.paginator import Paginator
from django.templatetags.static import static
import calendar
from django.views.decorators.http import require_POST
import re
from django.utils.html import strip_tags
from pathlib import Path


# -----------------------------------------------------------------
# VISTA DEL PADRE
# -----------------------------------------------------------------
@login_required
def padre_ver_desarrollo(request, nino_id):
    if request.user.rol.nombre_rol != 'padre':
        return redirect('role_redirect')

    try:
        padre = Padre.objects.get(usuario=request.user)
        # Obtener el niño específico y verificar que pertenece al padre
        nino = get_object_or_404(Nino, id=nino_id, padre=padre)

        desarrollos_qs = DesarrolloNino.objects.filter(nino=nino).order_by('-fecha_fin_mes')

        # Lógica de filtrado por mes
        mes_filtro = request.GET.get('mes', '')
        if mes_filtro:
            try:
                year, month = map(int, mes_filtro.split('-'))
                desarrollos_qs = desarrollos_qs.filter(fecha_fin_mes__year=year, fecha_fin_mes__month=month)
            except (ValueError, TypeError):
                mes_filtro = ''

        # Procesamiento de datos para añadir colores e íconos (como en el dashboard)
        desarrollos_list = []
        for desarrollo in desarrollos_qs:
            # Lógica simple para asignar color e ícono basado en el logro
            logro = (desarrollo.logro_mes or "").lower()
            if "alto" in logro:
                accent_color, icono = "#27ae60", "fas fa-star"
            elif "adecuado" in logro:
                accent_color, icono = "#f1c40f", "fas fa-check"
            else: # "En Proceso" o sin datos
                accent_color, icono = "#e74c3c", "fas fa-exclamation-triangle"
            
            desarrollos_list.append({'desarrollo': desarrollo, 'accent_color': accent_color, 'icono': icono})

        # --- ¡AQUÍ ESTÁ LA CORRECCIÓN CLAVE! ---
        # Se aplica la paginación a la lista de desarrollos
        paginator = Paginator(desarrollos_list, 2) # 2 registros por página
        page_number = request.GET.get('page')
        desarrollos_paginados = paginator.get_page(page_number)

        return render(request, 'padre/desarrollo_list.html', {
            'nino': nino, 
            'desarrollos': desarrollos_paginados, # Se envía el objeto paginado
            'filtros': {'mes': mes_filtro}
        })
    except (Padre.DoesNotExist, Nino.DoesNotExist):
        return redirect('padre_dashboard')

# -----------------------------------------------------------------
# CRUD DESARROLLO PARA MADRE COMUNITARIA
# -----------------------------------------------------------------
@login_required
def listar_desarrollos(request):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('role_redirect')
    try:
        hogar_madre = HogarComunitario.objects.get(madre__usuario=request.user)
    except HogarComunitario.DoesNotExist:
        return render(request, 'madre/desarrollo_list.html', {'error': 'No tienes un hogar asignado.'})

    desarrollos = DesarrolloNino.objects.filter(nino__hogar=hogar_madre).select_related('nino', 'nino__padre__usuario').order_by('-fecha_fin_mes')
    ninos_del_hogar = Nino.objects.filter(hogar=hogar_madre)

    # --- Lógica de Filtrado Mejorada ---
    nino_id_filtro = request.GET.get('nino', '')
    mes_filtro = request.GET.get('mes', '') # YYYY-MM
    nino_filtrado = None  # Inicializamos la variable

    if nino_id_filtro:
        desarrollos = desarrollos.filter(nino__id=nino_id_filtro)
        try:
            # Obtenemos el objeto del niño para pasarlo a la plantilla
            nino_filtrado = Nino.objects.get(id=nino_id_filtro, hogar=hogar_madre)
        except Nino.DoesNotExist:
            # Si el niño no existe o no pertenece al hogar, no hacemos nada
            pass

    if mes_filtro:
        try:
            year, month = map(int, mes_filtro.split('-'))
            desarrollos = desarrollos.filter(fecha_fin_mes__year=year, fecha_fin_mes__month=month)
        except (ValueError, TypeError):
            pass

    # === LÓGICA DE DIFERENCIACIÓN DE CARDS ===
    hoy = timezone.now().date()
    desarrollos_list = []
    from novedades.models import Novedad
    for desarrollo in desarrollos:
        logro = desarrollo.logro_mes

        # Badge/accent/icon
        if logro == 'Alto':
            desarrollo.badge = 'Excelente'
            desarrollo.accent = 'card-accent-excelente'
            desarrollo.icon = 'fa-seedling'
        elif logro == 'Adecuado':
            desarrollo.badge = 'Bueno'
            desarrollo.accent = 'card-accent-muybueno'
            desarrollo.icon = 'fa-child'
        elif logro == 'En Proceso':
            desarrollo.badge = 'Regular'
            desarrollo.accent = 'card-accent-regular'
            desarrollo.icon = 'fa-meh'
        else:
            desarrollo.badge = 'Sin Datos'
            desarrollo.accent = 'card-accent-malo'
            desarrollo.icon = 'fa-frown'

        # ¿Es del mes actual?
        if desarrollo.fecha_fin_mes.year == hoy.year and desarrollo.fecha_fin_mes.month == hoy.month:
            desarrollo.accent += ' card-accent-actual'
            desarrollo.is_actual = True
        else:
            desarrollo.is_actual = False

        # Obtener novedades del mes para el niño
        novedades_qs = Novedad.objects.filter(
            nino=desarrollo.nino,
            fecha__year=desarrollo.fecha_fin_mes.year,
            fecha__month=desarrollo.fecha_fin_mes.month
        ).order_by('fecha')
        if novedades_qs.exists():
            novedades_html = []
            for novedad in novedades_qs:
                tipo = novedad.get_tipo_display() if hasattr(novedad, 'get_tipo_display') else novedad.tipo
                # fecha = novedad.fecha.strftime('%d/%m/%Y')  # Eliminamos la fecha
                descripcion = novedad.descripcion or ''
                url = reverse('novedades:novedades_detail', args=[novedad.id])
                novedades_html.append(
                    f'<div style="margin-bottom:8px;"><b>{tipo}</b>: {descripcion} <a href="{url}" target="_blank" style="color:#5dade2;">Ver detalle</a></div>'
                )
            desarrollo.novedades_mes = "".join(novedades_html)
        else:
            desarrollo.novedades_mes = ""
        desarrollos_list.append(desarrollo)

    # --- Paginación ---
    paginator = Paginator(desarrollos_list, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    filtros = {
        'nino': nino_id_filtro,
        'mes': mes_filtro,
    }

    return render(request, 'madre/desarrollo_list.html', {
        'desarrollos': page_obj,
        'ninos': ninos_del_hogar,
        'nino_id_filtro': nino_id_filtro,
        'mes_filtro': mes_filtro,
        'nino_filtrado': nino_filtrado, # Pasamos el objeto del niño a la plantilla
        'filtros': filtros,
    })

@login_required
def generar_evaluacion_mensual(request):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('role_redirect')

    try:
        hogar_madre = HogarComunitario.objects.get(madre__usuario=request.user)
    except HogarComunitario.DoesNotExist:
        messages.error(request, "No tienes un hogar comunitario asignado.")
        return redirect('madre_dashboard')

    ninos_del_hogar = Nino.objects.filter(hogar=hogar_madre)

    if request.method == 'POST':
        nino_id = request.POST.get('nino')
        mes_str = request.POST.get('mes') # Formato YYYY-MM

        if not nino_id or not mes_str:
            messages.error(request, "Debes seleccionar un niño y un mes para generar la evaluación.")
            return redirect('desarrollo:generar_evaluacion')

        try:
            year, month = map(int, mes_str.split('-'))
            # Usamos el último día del mes para la fecha de referencia
            last_day = calendar.monthrange(year, month)[1]
            fecha_fin_mes = datetime(year, month, last_day).date()
        except ValueError:
            messages.error(request, "El formato del mes no es válido.")
            return redirect('desarrollo:generar_evaluacion')

        # Validar que no exista ya una evaluación para ese niño y mes
        nino = get_object_or_404(Nino, id=nino_id)
        if DesarrolloNino.objects.filter(nino_id=nino_id, fecha_fin_mes=fecha_fin_mes).exists():
            messages.warning(request, f"Ya existe una evaluación para {nino.nombres} en el mes seleccionado.")
            return redirect(reverse('desarrollo:listar_desarrollos') + f'?nino={nino_id}')

        # Crear la instancia. El método save() llamará al servicio de generación automática.
        try:
            nino = Nino.objects.get(id=nino_id)
            evaluacion = DesarrolloNino.objects.create(nino=nino, fecha_fin_mes=fecha_fin_mes)
            messages.success(request, f"Evaluación para {nino.nombres} del mes de {mes_str} generada exitosamente.")
            return redirect('desarrollo:ver_desarrollo', id=evaluacion.id)
        except Exception as e:
            messages.error(request, f"Ocurrió un error al generar la evaluación: {e}")
            return redirect('desarrollo:generar_evaluacion')

    return render(request, 'madre/desarrollo_form.html', {
        'ninos': ninos_del_hogar,
        'titulo_form': 'Generar Evaluación Mensual Automática',
        'form_action': reverse('desarrollo:generar_evaluacion'),
    })

@login_required
def ver_desarrollo(request, id):
    if request.user.rol.nombre_rol not in ['madre_comunitaria', 'padre']:
        return redirect('role_redirect')

    desarrollo = get_object_or_404(DesarrolloNino, id=id)

    # --- Lógica de Seguridad (sin cambios) ---
    if request.user.rol.nombre_rol == 'madre_comunitaria':
        if desarrollo.nino.hogar.madre.usuario != request.user:
            return redirect('desarrollo:listar_desarrollos')
    elif request.user.rol.nombre_rol == 'padre':
        if desarrollo.nino.padre.usuario != request.user:
            return redirect('padre_dashboard')
    
    # --- CORRECCIÓN ---
    # Redirigir a la vista de registro/edición que ya maneja la visualización.
    # Esto evita el error TemplateDoesNotExist y reutiliza la lógica existente.
    mes_str = desarrollo.fecha_fin_mes.strftime('%Y-%m')
    return redirect(reverse('desarrollo:registrar_desarrollo') + f'?nino={desarrollo.nino.id}&mes={mes_str}')


@login_required
def eliminar_desarrollo(request, id):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('role_redirect')

    desarrollo = get_object_or_404(DesarrolloNino, id=id)

    if desarrollo.nino.hogar.madre.usuario != request.user:
        return redirect('desarrollo:listar_desarrollos')

    nino_id = desarrollo.nino.id
    desarrollo.delete()
    messages.error(request, "¡El registro de desarrollo ha sido eliminado correctamente!")
    
    return redirect(reverse('desarrollo:listar_desarrollos') + f'?nino={nino_id}')

@require_POST
@login_required
def eliminar_desarrollos_seleccionados(request):
    """
    Vista para eliminar múltiples registros de desarrollo seleccionados mediante checkboxes.
    """
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('role_redirect')

    desarrollo_ids = request.POST.getlist('desarrollo_ids')
    nino_id_filtro = request.POST.get('nino_id_filtro')

    if not desarrollo_ids:
        messages.warning(request, "No has seleccionado ningún registro para eliminar.")
        return redirect('desarrollo:listar_desarrollos')

    # Seguridad: Asegurarse de que la madre solo pueda eliminar registros de su propio hogar.
    registros_a_eliminar = DesarrolloNino.objects.filter(
        id__in=desarrollo_ids,
        nino__hogar__madre__usuario=request.user
    )

    count = registros_a_eliminar.count()

    if count > 0:
        registros_a_eliminar.delete()
        messages.success(request, f"Se han eliminado {count} registros de desarrollo exitosamente.")

    # Construir la URL de redirección
    redirect_url = reverse('desarrollo:listar_desarrollos')
    if nino_id_filtro:
        redirect_url += f'?nino={nino_id_filtro}'
    
    return redirect(redirect_url)

@login_required
def generar_reporte(request):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('role_redirect')

    try:
        hogar_madre = HogarComunitario.objects.get(madre__usuario=request.user)
    except HogarComunitario.DoesNotExist:
        return render(request, 'madre/reporte_form.html', {'error': 'No tienes un hogar asignado.'})

    ninos_del_hogar = Nino.objects.filter(hogar=hogar_madre)
    context = {'ninos': ninos_del_hogar}

    if request.method == 'GET' and 'nino' in request.GET:
        nino_id = request.GET.get('nino')
        tipo_reporte = request.GET.get('tipo_reporte', 'ambos')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        if nino_id:
            nino_seleccionado = get_object_or_404(Nino, id=nino_id, hogar=hogar_madre)
            desarrollos = []
            novedades = []

            # Filtrar Desarrollos
            if tipo_reporte in ['desarrollos', 'ambos']:
                query_desarrollo = DesarrolloNino.objects.filter(nino=nino_seleccionado)
                if fecha_inicio:
                    query_desarrollo = query_desarrollo.filter(fecha_fin_mes__gte=fecha_inicio)
                if fecha_fin:
                    query_desarrollo = query_desarrollo.filter(fecha_fin_mes__lte=fecha_fin)
                desarrollos = query_desarrollo.order_by('fecha_fin_mes')

            # Filtrar Novedades
            if tipo_reporte in ['novedades', 'ambos']:
                query_novedad = Novedad.objects.filter(nino=nino_seleccionado)
                if fecha_inicio:
                    query_novedad = query_novedad.filter(fecha__gte=fecha_inicio)
                if fecha_fin:
                    query_novedad = query_novedad.filter(fecha__lte=fecha_fin)
                novedades = query_novedad.order_by('fecha')

            context.update({
                'nino_seleccionado': nino_seleccionado,
                'desarrollos': desarrollos,
                'novedades': novedades,
                'filtros': request.GET, # Pasa los filtros para mantenerlos en el form
                'mostrar_resumen': True
            })

    return render(request, 'madre/reporte_form.html', context)

@login_required
def reporte_resumen(request, nino_id):
    nino = get_object_or_404(Nino, id=nino_id)

    # Asegurarse de que la madre solo pueda ver niños de su hogar
    if not request.user.is_staff:
        try:
            hogar_madre = HogarComunitario.objects.get(madre__usuario=request.user)
            if nino.hogar != hogar_madre:
                return redirect('gestion_ninos')
        except HogarComunitario.DoesNotExist:
            return redirect('gestion_ninos')

    # --- Lógica de Filtrado ---
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')

    # Obtener todos los registros
    seguimientos_query = SeguimientoDiario.objects.filter(nino=nino)
    novedades = Novedad.objects.filter(nino=nino)
    desarrollos = DesarrolloNino.objects.filter(nino=nino)

    # Aplicar filtro de fecha de inicio si existe
    if fecha_inicio_str:
        seguimientos_query = seguimientos_query.filter(fecha__gte=fecha_inicio_str)
        novedades = novedades.filter(fecha__gte=fecha_inicio_str)
        desarrollos = desarrollos.filter(fecha_fin_mes__gte=fecha_inicio_str)

    # Aplicar filtro de fecha de fin si existe
    if fecha_fin_str:
        seguimientos_query = seguimientos_query.filter(fecha__lte=fecha_fin_str)
        novedades = novedades.filter(fecha__lte=fecha_fin_str)
        desarrollos = desarrollos.filter(fecha_fin_mes__lte=fecha_fin_str)

    context = {
        'nino': nino,
        'desarrollos': desarrollos.order_by('-fecha_fin_mes'),
        'novedades': novedades.order_by('-fecha'),
        'seguimientos': seguimientos_query.order_by('-fecha'),
    }
    return render(request, 'reporte/reporte_resumen.html', context)


@login_required
def generar_reporte_pdf(request, nino_id):
    nino = get_object_or_404(Nino, id=nino_id)

    tipo_reporte = request.GET.get('tipo_reporte', 'ambos')

    # Obtener fechas como strings
    fecha_inicio_str = request.GET.get('fecha_inicio') or None
    fecha_fin_str = request.GET.get('fecha_fin') or None

    # Convertir fechas SOLO si vienen
    def parse_fecha(f):
        try:
            return datetime.strptime(f, '%Y-%m-%d').date() if f else None
        except:
            return None

    fecha_inicio = parse_fecha(fecha_inicio_str)
    fecha_fin = parse_fecha(fecha_fin_str)

    # Base de consultas vacías
    desarrollos = DesarrolloNino.objects.none()
    novedades = Novedad.objects.none()
    seguimientos = SeguimientoDiario.objects.none()

    # Aplicar tipo de reporte
    if tipo_reporte in ['ambos', 'desarrollo']:
        desarrollos = DesarrolloNino.objects.filter(nino=nino)

    if tipo_reporte in ['ambos', 'novedades']:
        novedades = Novedad.objects.filter(nino=nino)

    if tipo_reporte in ['ambos', 'seguimiento']:
        seguimientos = SeguimientoDiario.objects.filter(nino=nino)

    # Aplicar filtros de fecha de forma SEGURA
    if fecha_inicio:
        desarrollos = desarrollos.filter(fecha_fin_mes__gte=fecha_inicio)
        novedades = novedades.filter(fecha__gte=fecha_inicio)
        seguimientos = seguimientos.filter(fecha__gte=fecha_inicio)

    if fecha_fin:
        desarrollos = desarrollos.filter(fecha_fin_mes__lte=fecha_fin)
        novedades = novedades.filter(fecha__lte=fecha_fin)
        seguimientos = seguimientos.filter(fecha__lte=fecha_fin)

    # --- CÁLCULO PARA LAS ESTRELLAS ---
    seguimientos = list(seguimientos.order_by('fecha'))
    for s in seguimientos:
        s.valoracion_restante = 5 - (s.valoracion or 0)

    logo_url = request.build_absolute_uri(static('img/logoSinFondo.png'))

    # Renderizar plantilla HTML
    template_path = 'reporte/reporte_pdf.html'
    context = {
        'nino': nino,
        'desarrollos': desarrollos.order_by('fecha_fin_mes'),
        'novedades': novedades.order_by('fecha'),
        'seguimientos': seguimientos,  # Ya es lista con el atributo extra
        'tipo_reporte': tipo_reporte,
        'fecha_inicio': fecha_inicio_str or "N/A",
        'fecha_fin': fecha_fin_str or "N/A",
        'logo_url': logo_url,
        'hogar_comunitario': nino.hogar,
        'usuario_generador': f"{request.user.nombres} {request.user.apellidos}".strip() or request.user.documento,
    }
    template = get_template(template_path)
    html = template.render(context)

    # Generar PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_{nino.nombres}_{nino.apellidos}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generando PDF. <pre>' + html + '</pre>')

    return response

@login_required
def generar_certificado_desarrollo_pdf(request, desarrollo_id):
    """
    Genera un certificado en PDF para un registro de desarrollo específico.
    """
    desarrollo = get_object_or_404(DesarrolloNino, id=desarrollo_id)
    nino = desarrollo.nino

    # --- Lógica de Seguridad ---
    if request.user.rol.nombre_rol == 'madre_comunitaria':
        if nino.hogar.madre.usuario != request.user:
            messages.error(request, "No tienes permiso para generar este certificado.")
            return redirect('desarrollo:listar_desarrollos')
    elif request.user.rol.nombre_rol == 'padre':
        if nino.padre.usuario != request.user:
            messages.error(request, "No tienes permiso para ver este certificado.")
            return redirect('padre_dashboard')
    else:
        messages.error(request, "Acceso no autorizado.")
        return redirect('home')

    # --- Mensajes Motivacionales según el Logro ---
    logro = desarrollo.logro_mes
    if logro == 'Alto':
        titulo_mensaje = "¡Un Logro Extraordinario!"
        mensaje = f"Tu dedicación y entusiasmo te han llevado a alcanzar un desempeño sobresaliente. Eres una estrella brillante que ilumina nuestro hogar cada día. ¡Sigue así, estamos muy orgullosos de ti!"
    elif logro == 'Adecuado':
        titulo_mensaje = "¡Vas por un Excelente Camino!"
        mensaje = f"Has demostrado un progreso maravilloso y un gran esfuerzo en tus actividades. Cada paso que das es importante y nos llena de alegría. ¡Sigue explorando, aprendiendo y divirtiéndote!"
    else: # 'En Proceso'
        titulo_mensaje = "¡Tu Esfuerzo es Valioso!"
        mensaje = f"Cada día es una nueva oportunidad para aprender y crecer. Valoramos mucho tu esfuerzo y perseverancia. Recuerda que cada paso, grande o pequeño, es un avance. ¡Estamos aquí para apoyarte siempre!"

    # --- Lógica para obtener el nombre del mes ---
    # 💡 CORRECCIÓN: Se añade la lógica para pasar el nombre del mes a la plantilla.
    from pathlib import Path
    import locale
    try:
        # Se establece el idioma a español para obtener el nombre del mes correctamente.
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, '') # Fallback si el locale no está disponible
    nombre_mes = desarrollo.fecha_fin_mes.strftime('%B').capitalize()

    # --- Rutas a las imágenes ---
    # 💡 CORRECCIÓN: Convertir las URLs estáticas a rutas absolutas del sistema de archivos
    # para que xhtml2pdf pueda encontrarlas directamente, evitando el uso de link_callback.
    try:
        # os.path.join construye la ruta correcta para el sistema operativo
        logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logoSinFondo.png')
    except Exception: # pragma: no cover
        logo_path = '' # Se asigna una cadena vacía si falla

    try:
        # --- CORRECCIÓN ---
        # Se construye la ruta absoluta a la imagen de fondo.
        # Luego, se convierte a un formato URI (file://...) que xhtml2pdf puede interpretar
        # correctamente para encontrar el archivo en el sistema local.
        from pathlib import Path

        ruta_img = os.path.join(settings.BASE_DIR, 'core', 'static', 'img', 'certificadoDesarrollo.jpg')
        fondo_url = Path(ruta_img).as_uri()  # Esto genera 'file:///C:/...'


    except Exception: # pragma: no cover
        fondo_url = '' # Se asigna una cadena vacía si falla

    # --- Renderizar plantilla HTML ---
    template_path = 'reporte/certificado_desarrollo_pdf.html'
    context = {
        'desarrollo': desarrollo,
        'nino': nino,
        'hogar': nino.hogar,
        'madre_comunitaria': nino.hogar.madre,
        'titulo_mensaje': titulo_mensaje,
        'mensaje': mensaje,
        'logo_url': logo_path,  # Se pasa la ruta del sistema de archivos
        'fondo_url': fondo_url, # Se pasa la ruta del sistema de archivos
        'nombre_mes': nombre_mes, # Se añade el nombre del mes al contexto
        'fecha_emision': timezone.now(),
    }
    template = get_template(template_path)
    html = template.render(context)

    # --- Generar PDF ---
    response = HttpResponse(content_type='application/pdf')
    # Con 'inline' se abre en el navegador, con 'attachment' se descarga.
    response['Content-Disposition'] = f'inline; filename="certificado_{nino.nombres}_{desarrollo.fecha_fin_mes.strftime("%Y-%m")}.pdf"'
    
    # Al pasar rutas de archivo absolutas, ya no necesitamos un 'link_callback'.
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar el certificado en PDF. <pre>' + html + '</pre>')

    return response

# -----------------------------------------------------------------
# CRUD SEGUIMIENTO DIARIO PARA MADRE COMUNITARIA
# -----------------------------------------------------------------
@login_required
def registrar_seguimiento_diario(request):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('role_redirect')

    try:
        hogar_madre = HogarComunitario.objects.get(madre__usuario=request.user)
    except HogarComunitario.DoesNotExist:
        return render(request, 'madre/seguimiento_diario_form.html', {'error': 'No tienes un hogar asignado.'})

    # --- Lógica para guardar el formulario (POST) ---
    if request.method == 'POST':
        fecha_str = request.POST.get('fecha')
        nino_id = request.POST.get('nino')

        # Validaciones iniciales
        if not nino_id:
            return render(request, 'madre/seguimiento_diario_form.html', {
                'error': "Por favor, selecciona un niño.",
                'fecha_filtro': fecha_str,
            })

        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return render(request, 'madre/seguimiento_diario_form.html', {'error': 'La fecha proporcionada no es válida.'})

        nino = get_object_or_404(Nino, id=nino_id, hogar=hogar_madre)

        # 1. Validar si existe planeación para la fecha
        planeacion_del_dia = PlaneacionModel.objects.filter(madre=hogar_madre.madre.usuario, fecha=fecha_obj).first()
        if not planeacion_del_dia:
            return render(request, 'madre/seguimiento_diario_form.html', {
                'error': f"No hay actividad planeada para el día {fecha_str}. No se puede registrar seguimiento.",
                'fecha_filtro': fecha_str,
            })

        # 2. Validar asistencia del niño
        asistencia = nino.asistencias.filter(fecha=fecha_obj).first()
        if not asistencia or asistencia.estado != 'Presente':
            return render(request, 'madre/seguimiento_diario_form.html', {
                'error': f"El niño {nino.nombres} no asistió el {fecha_str}, no se puede registrar seguimiento.",
                'fecha_filtro': fecha_str,
                'planeacion': planeacion_del_dia,
            })

        # 3. Validar que no exista un seguimiento duplicado
        if SeguimientoDiario.objects.filter(nino=nino, fecha=fecha_obj).exists():
            return render(request, 'madre/seguimiento_diario_form.html', {
                'error': f"Ya existe un seguimiento para {nino.nombres} en esta fecha.",
                'fecha_filtro': fecha_str,
                'planeacion': planeacion_del_dia,
                # FIX: Pasar el niño preseleccionado para que el botón "volver" funcione
                'nino_preseleccionado': nino,
                'paso': 'registrar_datos', # Para mantener la vista del formulario
                'ninos_para_seleccionar': [nino], # Para que el select no falle
            })
        # Crear el registro de seguimiento
        seguimiento = SeguimientoDiario.objects.create(
            nino=nino,
            planeacion=planeacion_del_dia,
            fecha=fecha_obj,
            comportamiento_general=request.POST.get('comportamiento_general'),
            estado_emocional=request.POST.get('estado_emocional'),
            observaciones=request.POST.get('observaciones'),
            observacion_relevante='observacion_relevante' in request.POST,
            valoracion=request.POST.get('valoracion')
        )

        # 4. Guardar las evaluaciones por dimensión
        dimensiones_ids = request.POST.getlist('dimension_id')
        for dim_id in dimensiones_ids:
            desempeno = request.POST.get(f'desempeno_{dim_id}')
            observacion_dim = request.POST.get(f'observacion_{dim_id}')
            
            if desempeno: # Solo guardar si se envió un desempeño
                EvaluacionDimension.objects.create(
                    seguimiento=seguimiento,
                    dimension_id=dim_id,
                    desempeno=desempeno,
                    observacion=observacion_dim
                )

        messages.success(request, f"¡Seguimiento para {nino.nombres} registrado correctamente!")
        redirect_url = reverse('desarrollo:listar_seguimientos')
        return redirect(f'{redirect_url}?nino={nino_id}')

    # --- Lógica para mostrar el formulario (GET) ---
    fecha_str = request.GET.get('fecha')
    nino_id_preseleccionado = request.GET.get('nino')
    context = {
        'titulo_form': 'Registrar Seguimiento Diario',
        'fecha_filtro': fecha_str,
        'nino_preseleccionado': None, # Inicializamos
        'comportamiento_choices': SeguimientoDiario.COMPORTAMIENTO_CHOICES,
        'estado_emocional_choices': SeguimientoDiario.ESTADO_EMOCIONAL_CHOICES,
    }

    # Si se preselecciona un niño (ej: desde la gestión), lo obtenemos y lo pasamos al contexto.
    if nino_id_preseleccionado:
        try:
            context['nino_preseleccionado'] = Nino.objects.get(id=nino_id_preseleccionado, hogar=hogar_madre)
        except Nino.DoesNotExist:
            pass # Si el niño no existe o no pertenece al hogar, simplemente no se preselecciona.

    # Si no se ha seleccionado una fecha, simplemente mostramos el selector de fecha.
    if not fecha_str:
        return render(request, 'madre/seguimiento_diario_form.html', context)

    # --- A partir de aquí, asumimos que SÍ hay una fecha ---
    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    # Precargar las dimensiones para optimizar la consulta
    planeacion_del_dia = PlaneacionModel.objects.filter(madre=hogar_madre.madre.usuario, fecha=fecha_obj).prefetch_related('dimensiones').first()
    if not planeacion_del_dia:
        context['error'] = f"No hay actividad planeada para este día ({fecha_str}). No se puede registrar seguimiento."
        return render(request, 'madre/seguimiento_diario_form.html', context)

    context['dimensiones_planeacion'] = planeacion_del_dia.dimensiones.all()

    # --- Verificación de asistencia específica si viene un niño preseleccionado ---
    if context.get('nino_preseleccionado'):
        nino_obj = context['nino_preseleccionado']
        asistencia = nino_obj.asistencias.filter(fecha=fecha_obj).first()
        
        if not asistencia:
            context['error'] = f"No se puede registrar seguimiento: Aún no se ha registrado la asistencia de {nino_obj.nombres} para el día {fecha_str}."
            return render(request, 'madre/seguimiento_diario_form.html', context) # Detiene y muestra el error

        # FIX: Validar si ya existe un seguimiento para este niño en esta fecha
        if SeguimientoDiario.objects.filter(nino=nino_obj, fecha=fecha_obj).exists():
            context['error'] = f"Ya existe un seguimiento registrado para {nino_obj.nombres} en la fecha {fecha_str}."
            # No mostramos el formulario de registro si ya existe.
            return render(request, 'madre/seguimiento_diario_form.html', context)

        
        if asistencia.estado != 'Presente':
            context['error'] = f"No se puede registrar seguimiento: El niño {nino_obj.nombres} fue registrado como '{asistencia.estado}' el día {fecha_str}."
            return render(request, 'madre/seguimiento_diario_form.html', context) # Detiene y muestra el error


    ninos_del_hogar = Nino.objects.filter(hogar=hogar_madre)
    ninos_disponibles = []
    for nino in ninos_del_hogar:
        asistio = nino.asistencias.filter(fecha=fecha_obj, estado='Presente').exists()
        ya_tiene_seguimiento = SeguimientoDiario.objects.filter(nino=nino, fecha=fecha_obj).exists()
        if asistio and not ya_tiene_seguimiento:
            ninos_disponibles.append(nino)

    # Si hay un niño preseleccionado que no está en la lista de disponibles, no mostramos el mensaje genérico.
    context.update({
        'planeacion': planeacion_del_dia,
        'ninos_para_seleccionar': ninos_disponibles,
        'paso': 'registrar_datos'
    })

    if not ninos_disponibles:
        if not context.get('nino_preseleccionado'):
            context['info'] = f"Todos los niños que asistieron el {fecha_str} ya tienen su seguimiento registrado o no hay niños disponibles."

    return render(request, 'madre/seguimiento_diario_form.html', context)

@login_required
def listar_seguimientos(request):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('role_redirect')

    try:
        hogar_madre = HogarComunitario.objects.get(madre__usuario=request.user)
    except HogarComunitario.DoesNotExist:
        return render(request, 'madre/seguimiento_diario_list.html', {'error': 'No tienes un hogar asignado.'})

    nino_id_filtro = request.GET.get('nino')
    fecha_str = request.GET.get('fecha')
    nino_filtrado = None

    # La consulta base siempre filtra por el hogar de la madre
    seguimientos_query = SeguimientoDiario.objects.filter(
        nino__hogar=hogar_madre
    ).select_related(
        'nino', 'planeacion'
    ).prefetch_related('evaluaciones_dimension').order_by('-fecha')

    # Si se especifica un niño, se convierte en el filtro principal
    if nino_id_filtro:
        seguimientos_query = seguimientos_query.filter(nino__id=nino_id_filtro)
        try:
            nino_filtrado = Nino.objects.get(id=nino_id_filtro)
        except Nino.DoesNotExist:
            pass # No se encontró el niño

    # Si se especifica una fecha, se usa como filtro secundario
    if fecha_str:
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            seguimientos_query = seguimientos_query.filter(fecha=fecha_obj)
        except (ValueError, TypeError):
            fecha_str = None # Ignorar fecha inválida
    else:
        # Si no hay fecha, no se filtra por fecha, mostrando todos los seguimientos del niño (si aplica)
        fecha_str = None

    # --- Paginación ---
    paginator = Paginator(seguimientos_query, 3) # Mostrar 6 seguimientos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    filtros = {
        'nino': nino_id_filtro,
        'fecha': fecha_str,
    }
    
    return render(request, 'madre/seguimiento_diario_list.html', {
        'seguimientos': page_obj, # Pasamos el objeto de página a la plantilla
        'fecha_filtro': fecha_str,
        'nino_id_filtro': nino_id_filtro,
        'nino_filtrado': nino_filtrado,
        'filtros': filtros,
    })

@login_required
def editar_seguimiento_diario(request, id):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('role_redirect')

    seguimiento = get_object_or_404(SeguimientoDiario, id=id)

    # Verificación de seguridad: la madre solo puede editar registros de su hogar.
    if seguimiento.nino.hogar.madre.usuario != request.user:
        messages.error(request, "No tienes permiso para editar este seguimiento.")
        return redirect('desarrollo:listar_seguimientos')

    if request.method == 'POST':
        # Actualizar campos principales del seguimiento
        seguimiento.comportamiento_general = request.POST.get('comportamiento_general')
        seguimiento.estado_emocional = request.POST.get('estado_emocional')
        seguimiento.observaciones = request.POST.get('observaciones')
        seguimiento.observacion_relevante = 'observacion_relevante' in request.POST
        seguimiento.valoracion = request.POST.get('valoracion')
        seguimiento.save()

        # Actualizar las evaluaciones por dimensión
        dimensiones_ids = request.POST.getlist('dimension_id')
        for dim_id in dimensiones_ids:
            desempeno = request.POST.get(f'desempeno_{dim_id}')
            observacion_dim = request.POST.get(f'observacion_{dim_id}')
            
            # Usamos update_or_create para actualizar si existe, o crear si es nueva
            if desempeno:
                EvaluacionDimension.objects.update_or_create(
                    seguimiento=seguimiento,
                    dimension_id=dim_id,
                    defaults={
                        'desempeno': desempeno,
                        'observacion': observacion_dim
                    }
                )

        messages.success(request, f"El seguimiento para {seguimiento.nino.nombres} del {seguimiento.fecha.strftime('%d-%m-%Y')} ha sido actualizado exitosamente.")
        return redirect(reverse('desarrollo:listar_seguimientos') + f'?nino={seguimiento.nino.id}')

    # --- Lógica para GET (mostrar el formulario con datos) ---
    # Precargar las dimensiones de la planeación asociada
    planeacion_del_dia = seguimiento.planeacion
    dimensiones_planeacion = planeacion_del_dia.dimensiones.all()

    # Cargar las evaluaciones de dimensión existentes en un diccionario para fácil acceso
    evaluaciones_existentes = {
        eval_dim.dimension_id: eval_dim 
        for eval_dim in seguimiento.evaluaciones_dimension.all()
    }

    # Añadir las evaluaciones existentes a cada dimensión para la plantilla
    for dim in dimensiones_planeacion:
        dim.evaluacion_guardada = evaluaciones_existentes.get(dim.id)

    return render(request, 'madre/editar_seguimiento_diario.html', {
        'seguimiento': seguimiento,
        'titulo_form': 'Editar Seguimiento Diario',
        'planeacion': planeacion_del_dia,
        'dimensiones_planeacion': dimensiones_planeacion,
        'comportamiento_choices': SeguimientoDiario.COMPORTAMIENTO_CHOICES,
        'estado_emocional_choices': SeguimientoDiario.ESTADO_EMOCIONAL_CHOICES,
    })

@login_required
def eliminar_seguimiento(request, id):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('role_redirect')

    seguimiento = get_object_or_404(SeguimientoDiario, id=id)

    # Seguridad: solo la madre del hogar puede eliminar
    if seguimiento.nino.hogar.madre.usuario != request.user:
        return redirect('desarrollo:listar_seguimientos')

    nino_id = seguimiento.nino.id
    fecha_seguimiento = seguimiento.fecha.strftime('%Y-%m-%d')
    seguimiento.delete()
    messages.error(request, f"El seguimiento del {fecha_seguimiento} para {seguimiento.nino.nombres} ha sido eliminado.")
    
    # Redirigir a la lista de seguimientos del niño específico
    redirect_url = reverse('desarrollo:listar_seguimientos')
    return redirect(f'{redirect_url}?nino={nino_id}')


@login_required
@require_POST
def eliminar_seguimientos_lote(request):
    """
    Vista para eliminar múltiples registros de seguimiento diario seleccionados.
    """
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('role_redirect')

    seguimiento_ids = request.POST.getlist('seguimiento_ids')
    if not seguimiento_ids:
        messages.warning(request, 'No se seleccionó ningún seguimiento para eliminar.')
    else:
        try:
            # Seguridad: Asegurarse de que la madre solo pueda eliminar seguimientos de su propio hogar.
            seguimientos_a_eliminar = SeguimientoDiario.objects.filter(id__in=seguimiento_ids, nino__hogar__madre__usuario=request.user)
            count = seguimientos_a_eliminar.count()
            seguimientos_a_eliminar.delete()
            messages.success(request, f'Se eliminaron {count} seguimientos exitosamente.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al intentar eliminar los seguimientos: {e}')
    
    # Redirigir a la misma página, manteniendo el filtro de niño si existe
    nino_id = request.POST.get('nino_id')
    redirect_url = reverse('desarrollo:listar_seguimientos')
    return redirect(f'{redirect_url}?nino={nino_id}' if nino_id else redirect_url)


@login_required
def registrar_desarrollo(request):
    if request.user.rol.nombre_rol != 'madre_comunitaria':
        return redirect('home')
    try:
        madre_comunitaria = MadreComunitaria.objects.get(usuario=request.user)
        hogar_madre = HogarComunitario.objects.get(madre=madre_comunitaria)
    except HogarComunitario.DoesNotExist:
        messages.error(request, 'No tienes un hogar asignado.')
        return redirect('home')
    
    ninos_del_hogar = Nino.objects.filter(hogar=hogar_madre)

    if request.method == 'POST':
        desarrollo_id = request.POST.get('desarrollo_id')
        nino_id = request.POST.get('nino_hidden') or request.POST.get('nino')
        mes_str = request.POST.get('mes_hidden') or request.POST.get('mes')

        if not nino_id or not mes_str:
            messages.error(request, "Debes seleccionar un niño y un mes.")
            return redirect('desarrollo:listar_desarrollos')

        nino = get_object_or_404(Nino, id=nino_id, hogar=hogar_madre)
        try:
            year, month = map(int, mes_str.split('-'))
            last_day = calendar.monthrange(year, month)[1]
            fecha_fin_mes = datetime(year, month, last_day).date()
        except (ValueError, TypeError):
            messages.error(request, "El formato del mes es inválido.")
            return redirect('desarrollo:listar_desarrollos')

        # --- ACCIÓN: GUARDAR (Crear o Actualizar) ---
        # Esta acción se dispara si hay un 'desarrollo_id' (actualización) o si
        # el formulario que se envía es el de "Guardar Registro" (creación).
        # Usamos 'nino_hidden' como indicador de que estamos en el paso 2.
        if 'nino_hidden' in request.POST:
            from .services import GeneradorEvaluacionMensual

            # Si hay ID, es una ACTUALIZACIÓN.
            if desarrollo_id:
                desarrollo = get_object_or_404(DesarrolloNino, id=desarrollo_id, nino=nino)
                # Actualizar solo los campos manuales y los editables
                desarrollo.evaluacion_cognitiva = request.POST.get('evaluacion_cognitiva', '')
                desarrollo.evaluacion_comunicativa = request.POST.get('evaluacion_comunicativa', '')
                desarrollo.evaluacion_socio_afectiva = request.POST.get('evaluacion_socio_afectiva', '')
                desarrollo.evaluacion_corporal = request.POST.get('evaluacion_corporal', '')
                desarrollo.evaluacion_autonomia = request.POST.get('evaluacion_autonomia', '')
                desarrollo.fortalezas_mes = request.POST.get('fortalezas_mes', '')
                desarrollo.aspectos_a_mejorar = request.POST.get('aspectos_a_mejorar', '')
                desarrollo.alertas_mes = request.POST.get('alertas_mes', '')
                desarrollo.conclusion_general = request.POST.get('conclusion_general', '')
                desarrollo.observaciones_adicionales = request.POST.get('observaciones_adicionales', '')
                desarrollo.recomendaciones_personales = request.POST.get('recomendaciones_personales', '')
                
                # --- LÓGICA AUTOMÁTICA DE ALERTAS GENERALES ---
                # Analizar seguimientos del mes para alertas generales
                seguimientos_mes = SeguimientoDiario.objects.filter(
                    nino=nino,
                    fecha__year=fecha_fin_mes.year,
                    fecha__month=fecha_fin_mes.month
                )
                alertas_generales = []
                # Bajón de rendimiento: comparar promedio con mes anterior
                valoraciones = [s.valoracion for s in seguimientos_mes if s.valoracion is not None]
                if valoraciones:
                    promedio_actual = sum(valoraciones) / len(valoraciones)
                    # Buscar mes anterior
                    mes_anterior = fecha_fin_mes - relativedelta(months=1)
                    seguimientos_anteriores = SeguimientoDiario.objects.filter(
                        nino=nino,
                        fecha__year=mes_anterior.year,
                        fecha__month=mes_anterior.month
                    )
                    valoraciones_anteriores = [s.valoracion for s in seguimientos_anteriores if s.valoracion is not None]
                    if valoraciones_anteriores:
                        promedio_anterior = sum(valoraciones_anteriores) / len(valoraciones_anteriores)
                        if promedio_actual < promedio_anterior - 1: # Bajón significativo
                            alertas_generales.append(
                                f"Alerta: Se detecta un bajón de rendimiento este mes (promedio {promedio_actual:.1f} vs {promedio_anterior:.1f} el mes anterior)."
                            )
                # Cambios de humor negativos frecuentes
                estados_negativos = [s.estado_emocional for s in seguimientos_mes if s.estado_emocional in ['Triste', 'Enojado', 'Ansioso', 'Irritable']]
                if len(estados_negativos) >= 3:
                    alertas_generales.append(
                        f"Alerta: Se observan cambios de humor negativos frecuentes ({len(estados_negativos)} días con estado emocional negativo)."
                    )
                # Agregar otras reglas automáticas aquí si se requiere
                # Unir alertas automáticas con las manuales
                if alertas_generales:
                    desarrollo.alertas_mes = (desarrollo.alertas_mes or '') + '\n' + '\n'.join(alertas_generales)
                desarrollo.save(run_generator=False) # Guardar sin regenerar todo
                messages.success(request, f'El registro de {nino.nombres} se actualizó exitosamente.')

            # Si NO hay ID, es una CREACIÓN.
            else:
                # Validar que no exista ya uno para evitar duplicados si el usuario juega con el formulario
                if DesarrolloNino.objects.filter(nino=nino, fecha_fin_mes=fecha_fin_mes).exists():
                    messages.warning(request, f'Ya existe un registro para {nino.nombres} en este mes.')
                    return redirect(reverse('desarrollo:listar_desarrollos') + f'?nino={nino.id}')
                
                # 1. Crear la instancia y guardarla. Esto ejecuta el generador automático.
                desarrollo = DesarrolloNino.objects.create(nino=nino, fecha_fin_mes=fecha_fin_mes)
                desarrollo.refresh_from_db() # Recargamos para tener los datos generados
                
                # 2. Actualizar la instancia con los datos del formulario (tus ediciones).
                #    Esto sobreescribe los valores automáticos con tus valores.
                desarrollo.evaluacion_cognitiva = request.POST.get('evaluacion_cognitiva', desarrollo.evaluacion_cognitiva)
                desarrollo.evaluacion_comunicativa = request.POST.get('evaluacion_comunicativa', desarrollo.evaluacion_comunicativa)
                desarrollo.evaluacion_socio_afectiva = request.POST.get('evaluacion_socio_afectiva', desarrollo.evaluacion_socio_afectiva)
                desarrollo.evaluacion_corporal = request.POST.get('evaluacion_corporal', desarrollo.evaluacion_corporal)
                desarrollo.evaluacion_autonomia = request.POST.get('evaluacion_autonomia', desarrollo.evaluacion_autonomia)
                desarrollo.fortalezas_mes = request.POST.get('fortalezas_mes', desarrollo.fortalezas_mes)
                desarrollo.aspectos_a_mejorar = request.POST.get('aspectos_a_mejorar', desarrollo.aspectos_a_mejorar)
                desarrollo.alertas_mes = request.POST.get('alertas_mes', desarrollo.alertas_mes)
                desarrollo.conclusion_general = request.POST.get('conclusion_general', desarrollo.conclusion_general)
                desarrollo.observaciones_adicionales = request.POST.get('observaciones_adicionales', '')
                desarrollo.recomendaciones_personales = request.POST.get('recomendaciones_personales', '')
                
                # 3. Guardar los cambios finales sin volver a ejecutar el generador.
                desarrollo.save(run_generator=False)
                messages.success(request, f'El registro para {nino.nombres} se guardó exitosamente.')

            # Recalcular tendencia del mes siguiente en ambos casos (crear/actualizar)
            fecha_mes_siguiente = desarrollo.fecha_fin_mes + relativedelta(months=1)
            desarrollo_siguiente = DesarrolloNino.objects.filter(nino=nino, fecha_fin_mes__year=fecha_mes_siguiente.year, fecha_fin_mes__month=fecha_mes_siguiente.month).first()
            if desarrollo_siguiente:
                GeneradorEvaluacionMensual(desarrollo_siguiente).run(only_tendencia=True)

            return redirect(reverse('desarrollo:listar_desarrollos') + f'?nino={nino.id}')

        # --- ACCIÓN: GENERAR (Sin Guardar) ---
        else:
            # Validaciones antes de generar
            if not SeguimientoDiario.objects.filter(nino=nino, fecha__year=fecha_fin_mes.year, fecha__month=fecha_fin_mes.month).exists():
                messages.error(request, f'No se puede generar el informe para {nino.nombres} porque no tiene seguimientos diarios registrados en ese mes.')
                return redirect(reverse('desarrollo:listar_desarrollos') + f'?nino={nino.id}')

            # FIX: Esta validación debe ir DESPUÉS de la de seguimientos.
            if DesarrolloNino.objects.filter(nino=nino, fecha_fin_mes=fecha_fin_mes).exists():
                messages.error(request, f'Ya existe un registro para {nino.nombres} en este mes. Si desea modificarlo, por favor edítelo desde el listado.')
                return redirect(reverse('desarrollo:listar_desarrollos') + f'?nino={nino.id}')

            # Crear objeto EN MEMORIA (sin guardar)
            desarrollo_preview = DesarrolloNino(nino=nino, fecha_fin_mes=fecha_fin_mes)
            
            # Ejecutar el generador en la instancia en memoria
            from .services import GeneradorEvaluacionMensual
            # El generador necesita una instancia, pero no la guardará si le decimos que no
            generador = GeneradorEvaluacionMensual(desarrollo_preview)
            generador.run(save_instance=False) # Método modificado para no guardar

            # Contadores para la vista previa
            seguimientos_count = generador.seguimientos_mes.count()
            novedades_count = generador.novedades_mes.count()

            # Renderizar el formulario con los datos generados, listo para ser guardado
            return render(request, 'madre/desarrollo_form.html', {
                'titulo_form': f'Revisar y Guardar Desarrollo para {nino.nombres}',
                'desarrollo': desarrollo_preview, # El objeto sin ID
                'ninos': ninos_del_hogar,
                'form_action': reverse('desarrollo:registrar_desarrollo'),
                'seguimientos_mes_count': seguimientos_count,
                'novedades_mes_count': novedades_count,
                'alertas_novedades': getattr(desarrollo_preview, '_alertas_novedades', []),
            })

    # GET: mostrar formulario de selección de niño y mes
    nino_preseleccionado = None
    nino_id_get = request.GET.get('nino')
    mes_get = request.GET.get('mes')

    # Si vienen los parámetros, es para ver/editar un registro existente
    if nino_id_get and mes_get:
        try:
            year, month = map(int, mes_get.split('-'))
            last_day = calendar.monthrange(year, month)[1]
            fecha_fin_mes = datetime(year, month, last_day).date()
            
            desarrollo_existente = DesarrolloNino.objects.get(nino_id=nino_id_get, fecha_fin_mes=fecha_fin_mes)
            
            # Si se encuentra un registro, se renderiza el formulario en modo edición.
            # Contadores para la vista de edición.
            seguimientos_mes_count = SeguimientoDiario.objects.filter( 
                nino=desarrollo_existente.nino, 
                fecha__year=fecha_fin_mes.year, 
                fecha__month=fecha_fin_mes.month
            ).count()
            novedades_mes_count = Novedad.objects.filter(
                nino=desarrollo_existente.nino, 
                fecha__year=fecha_fin_mes.year, 
                fecha__month=fecha_fin_mes.month
            ).count()
            
            # --- CORRECCIÓN: Cargar las novedades para la vista previa en modo edición ---
            alertas_novedades = Novedad.objects.filter(
                nino=desarrollo_existente.nino,
                fecha__year=fecha_fin_mes.year,
                fecha__month=fecha_fin_mes.month
            ).order_by('fecha')

            # Renderizar el formulario con el registro existente para edición
            return render(request, 'madre/desarrollo_form.html', {
                'desarrollo': desarrollo_existente, 
                'titulo_form': f'Editar Desarrollo para {desarrollo_existente.nino.nombres}',
                'seguimientos_mes_count': seguimientos_mes_count,
                'novedades_mes_count': novedades_mes_count,
                'form_action': reverse('desarrollo:registrar_desarrollo'),
                # Pasamos las novedades consultadas a la plantilla
                'alertas_novedades': alertas_novedades,
            })
        except (DesarrolloNino.DoesNotExist, ValueError):
            # Si no existe, redirigimos para evitar errores, mostrando un mensaje.
            messages.info(request, "No se encontró un registro para ese niño y mes. Puede generar uno nuevo.")
            return redirect(reverse('desarrollo:registrar_desarrollo') + f'?nino={nino_id_get}')

    if nino_id_get:
        nino_preseleccionado = get_object_or_404(Nino, id=nino_id_get, hogar=hogar_madre)

    return render(request, 'madre/desarrollo_form.html', {
        'titulo_form': 'Generar Desarrollo Mensual',
        'ninos': ninos_del_hogar,
        'nino_preseleccionado': nino_preseleccionado,
        'form_action': reverse('desarrollo:registrar_desarrollo'),
    })

    # Procesar alertas para el contexto de la plantilla
    alertas_mes = desarrollo.alertas_mes or ""
    lineas = alertas_mes.splitlines()

    alertas_generales = []
    alertas_criticas = []

    for linea in lineas:
        if "Ver detalle:" in linea:
            alertas_criticas.append(linea)
        else:
            # Limpia HTML para el textarea
            texto_plano = strip_tags(linea).strip()
            if texto_plano:
                alertas_generales.append(texto_plano)

    context['alertas_generales'] = "\n".join(alertas_generales)
    context['alertas_criticas'] = alertas_criticas

    # Procesar alertas para el contexto de la plantilla
    alertas_mes = desarrollo.alertas_mes or ""
    lineas = alertas_mes.splitlines()

    alertas_generales = []
    alertas_criticas = []

    for linea in lineas:
        if "Ver detalle:" in linea:
            alertas_criticas.append(linea)
        else:
            # Limpia HTML para el textarea
            texto_plano = strip_tags(linea).strip()
            if texto_plano:
                alertas_generales.append(texto_plano)

    context['alertas_generales'] = "\n".join(alertas_generales)
    context['alertas_criticas'] = alertas_criticas