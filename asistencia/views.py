from django.shortcuts import render, redirect, get_object_or_404
from core.models import Nino, Asistencia
from datetime import date
from novedades.models import Novedad
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json
from notifications.models import Notification  # importa el modelo
from django.contrib.auth.decorators import login_required
from core.views import rol_requerido  # si lo tienes definido ahí
from core.models import HogarComunitario
from asistencia.utils import verificar_ausencias
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa




@login_required
@rol_requerido('madre_comunitaria')
def asistencia_form(request):
    madre_profile = request.user.madre_profile
    hogar_madre = HogarComunitario.objects.filter(madre=madre_profile).first()
    ninos = Nino.objects.filter(hogar=hogar_madre)

    if request.method == 'POST':
        fecha_str = request.POST.get('fecha')
        fecha_hoy = date.fromisoformat(fecha_str) if fecha_str else date.today()

        for nino in ninos:
            estado = request.POST.get(f'nino_{nino.id}')
            if estado:
                Asistencia.objects.update_or_create(
                    nino=nino,
                    fecha=fecha_hoy,
                    defaults={'estado': estado}
                )
                verificar_ausencias(nino, request.user)  # Verifica ausencias después de guardar

        # 🔔 Notificaciones del usuario
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        notif_count = notifications.filter(read=False).count()

        return render(request, 'asistencia/asistencia_form.html', {
            'ninos': ninos,
            'fecha_hoy': fecha_hoy.strftime('%Y-%m-%d'),
            'mensaje': 'Asistencia registrada exitosamente ✅',
            'notifications': notifications,
            'notif_count': notif_count,
        })

    fecha_hoy = date.today().strftime('%Y-%m-%d')
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    notif_count = notifications.filter(read=False).count()

    return render(request, 'asistencia/asistencia_form.html', {
        'ninos': ninos,
        'fecha_hoy': fecha_hoy,
        'notifications': notifications,
        'notif_count': notif_count,
    })




@login_required
@rol_requerido('madre_comunitaria')
def historial_asistencia(request, nino_id):
    madre_profile = request.user.madre_profile
    hogar_madre = HogarComunitario.objects.filter(madre=madre_profile).first()
    nino = get_object_or_404(Nino, id=nino_id, hogar=hogar_madre)
    historial = Asistencia.objects.filter(nino=nino).order_by('-fecha')

    # Filtro por rango
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        historial = historial.filter(fecha__range=[start_date, end_date])

    # Vincular novedad por fecha y niño
    for asistencia in historial:
        novedad = Novedad.objects.filter(nino=nino, fecha=asistencia.fecha).first()
        asistencia.novedad_id = novedad.id if novedad else None

    # Datos para calendario
    eventos = [
        {
            "title": a.estado,
            "start": a.fecha.strftime("%Y-%m-%d"),
            "color": (
                "#28a745" if a.estado == "Presente" else
                "#dc3545" if a.estado == "Ausente" else
                "#6f42c1"
            )
        }
        for a in historial
    ]

    total = historial.count()
    presentes = historial.filter(estado="Presente").count()
    ausentes = historial.filter(estado="Ausente").count()
    justificados = historial.filter(estado="Justificado").count()

    def porcentaje(valor):
        return round((valor / total) * 100) if total > 0 else 0

    return render(request, 'asistencia/historial.html', {
        'nino': nino,
        'historial': historial,
        'presentes': presentes,
        'ausentes': ausentes,
        'justificados': justificados,
        'porc_presentes': porcentaje(presentes),
        'porc_ausentes': porcentaje(ausentes),
        'porc_justificados': porcentaje(justificados),
        'eventos_json': json.dumps(eventos, cls=DjangoJSONEncoder),
        'start_date': start_date,
        'end_date': end_date,
    })


def crear_novedad_desde_asistencia(request):
    if request.method == 'POST':
        nino_id = request.POST.get('nino_id')
        fecha = request.POST.get('fecha')
        tipo = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion')
        observaciones = request.POST.get('observaciones')
        archivo_pdf = request.FILES.get('archivo_pdf')

        Novedad.objects.create(
            nino_id=nino_id,
            fecha=fecha,
            tipo=tipo,
            descripcion=descripcion,
            observaciones=observaciones,
            archivo_pdf=archivo_pdf
        )

        updated = Asistencia.objects.filter(nino_id=nino_id, fecha=fecha).update(estado="Justificado")
        if not updated:
            Asistencia.objects.create(nino_id=nino_id, fecha=fecha, estado="Justificado")

        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@login_required
@rol_requerido('madre_comunitaria')
def historial_asistencia_pdf(request, nino_id):
    madre_profile = request.user.madre_profile
    hogar_madre = HogarComunitario.objects.filter(madre=madre_profile).first()
    nino = get_object_or_404(Nino, id=nino_id, hogar=hogar_madre)
    historial = Asistencia.objects.filter(nino=nino).order_by('-fecha')

    # Contexto igual al HTML
    context = {
        'nino': nino,
        'historial': historial,
        'presentes': historial.filter(estado="Presente").count(),
        'ausentes': historial.filter(estado="Ausente").count(),
        'justificados': historial.filter(estado="Justificado").count(),
    }

    template = get_template("asistencia/historial_pdf.html")  # nuevo template para PDF
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="historial_{nino.nombres}.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response