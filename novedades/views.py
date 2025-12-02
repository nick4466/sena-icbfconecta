from django.shortcuts import render, get_object_or_404, redirect
from .models import Novedad
from .forms import NovedadForm
from django.db.models import Q
from datetime import datetime
from core.models import Nino, Asistencia, HogarComunitario
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.views import rol_requerido
from datetime import datetime
from django.utils.dateparse import parse_date


@login_required
@rol_requerido('madre_comunitaria')
def novedades_list(request):
    madre_profile = request.user.madre_profile
    hogar_madre = HogarComunitario.objects.filter(madre=madre_profile).first()
    ninos_madre = Nino.objects.filter(hogar=hogar_madre)

    query = request.GET.get('q')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    novedades = Novedad.objects.select_related('nino').filter(nino__in=ninos_madre).order_by('-fecha')

    # Filtro por texto
    if query:
        filtros = (
            Q(nino__nombres__icontains=query) |
            Q(nino__apellidos__icontains=query) |
            Q(tipo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(clase__icontains=query)
        )
        try:
            fecha_busqueda = datetime.strptime(query, "%d/%m/%Y").date()
            filtros |= Q(fecha=fecha_busqueda)
        except ValueError:
            pass

        novedades = novedades.filter(filtros)

    # Filtro por rango de fechas
    if fecha_inicio:
        novedades = novedades.filter(fecha__gte=parse_date(fecha_inicio))
    if fecha_fin:
        novedades = novedades.filter(fecha__lte=parse_date(fecha_fin))

    context = {
        'novedades': novedades,
        'query': query,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'novedades/list.html', context)



@login_required
@rol_requerido('madre_comunitaria')
def novedades_create(request):
    madre_profile = request.user.madre_profile
    hogar_madre = HogarComunitario.objects.filter(madre=madre_profile).first()

    form = NovedadForm(request.POST or None)
    form.fields['nino'].queryset = Nino.objects.filter(hogar=hogar_madre)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('novedades:novedades_list')

    return render(request, 'novedades/create.html', {'form': form})



@login_required
@rol_requerido('madre_comunitaria')
def novedades_edit(request, pk):
    madre_profile = request.user.madre_profile
    hogar_madre = HogarComunitario.objects.filter(madre=madre_profile).first()

    novedad = get_object_or_404(Novedad, pk=pk, nino__hogar=hogar_madre)
    form = NovedadForm(request.POST or None, instance=novedad)
    form.fields['nino'].queryset = Nino.objects.filter(hogar=hogar_madre)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('novedades:novedades_list')

    return render(request, 'novedades/form.html', {'form': form})


def novedades_delete(request, pk):
    novedad = get_object_or_404(Novedad, pk=pk)
    if request.method == 'POST':
        novedad.delete()
        return redirect('novedades:novedades_list')
    return render(request, 'novedades/confirm_delete.html', {'novedad': novedad})


def novedades_detail(request, pk):
    novedad = get_object_or_404(Novedad, pk=pk)
    return render(request, 'novedades/detail.html', {'novedad': novedad})  # corregido


def justificar_ausencia(request, novedad_id):
    novedad = get_object_or_404(Novedad, id=novedad_id)
    novedad.ausencia_justificada = True
    novedad.save()
    Asistencia.objects.filter(nino=novedad.nino, fecha=novedad.fecha).update(estado="Justificado")
    return redirect('novedades:novedades_list')  # corregido


@login_required
@rol_requerido('madre_comunitaria')
def nueva_novedad(request):
    madre_profile = request.user.madre_profile
    hogar_madre = HogarComunitario.objects.filter(madre=madre_profile).first()
    nino_id = request.GET.get('nino_id')
    fecha = request.GET.get('fecha')

    initial = {}
    nino = None
    if nino_id:
        nino = get_object_or_404(Nino, id=nino_id, hogar=hogar_madre)
        initial['nino'] = nino

    if request.method == 'POST':
        form = NovedadForm(request.POST or None, initial=initial)
        form.fields['nino'].queryset = Nino.objects.filter(hogar=hogar_madre)

        if form.is_valid():
            novedad = form.save()
            if nino_id and fecha:
                updated = Asistencia.objects.filter(nino_id=nino_id, fecha=fecha).update(estado="Justificado")
                if not updated:
                    Asistencia.objects.create(nino_id=nino_id, fecha=fecha, estado="Justificado")
                messages.success(request, "Novedad registrada y ausencia justificada.")
            return redirect('novedades:novedades_list')
    else:
        form = NovedadForm(initial=initial)
        form.fields['nino'].queryset = Nino.objects.filter(hogar=hogar_madre)

    return render(request, 'novedades/nueva.html', {'form': form, 'nino': nino, 'fecha': fecha})
  # corregido


@login_required
@rol_requerido('madre_comunitaria')
def detalle_novedad(request, novedad_id):
    madre_profile = request.user.madre_profile
    hogar_madre = HogarComunitario.objects.filter(madre=madre_profile).first()
    novedad = get_object_or_404(Novedad, id=novedad_id, nino__hogar=hogar_madre)
    return render(request, 'novedades/detalle.html', {'novedad': novedad})


from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from novedades.models import Novedad

from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404
from core.views import rol_requerido
from django.contrib.auth.decorators import login_required
from novedades.models import Novedad

@login_required
@rol_requerido('madre_comunitaria')
def novedades_pdf(request, novedad_id):
    novedad = get_object_or_404(Novedad, id=novedad_id)

    context = {
        'novedad': novedad,
    }

    template = get_template("novedades/novedades_pdf.html")  # <-- plural
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="novedad_{novedad.id}.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response
