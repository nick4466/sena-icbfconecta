from django.contrib.auth.decorators import login_required
from .models import Documentacion, Planeacion
from .forms import DocumentacionForm, PlaneacionForm
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.contrib import messages
from reportlab.pdfgen import canvas
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator



#Holaaaaa amiguitos de youtu :D
@login_required
def lista_planeaciones(request):
    madre = request.user
    mes = request.GET.get('mes')  # filtro por mes

    if mes:
        planeaciones = Planeacion.objects.filter(madre=madre, fecha__month=mes).order_by('-fecha')
    else:
        planeaciones = Planeacion.objects.filter(madre=madre).order_by('-fecha')
 # ------ PAGINACIÓN ------
    paginator = Paginator(planeaciones, 4)  # 4 planeaciones por página
    page_number = request.GET.get('page')
    planeaciones = paginator.get_page(page_number)
    # -------------------------

    # Lista de meses para la barra de búsqueda
    meses = [
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
        ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
        ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ]

    context = {
        'planeaciones': planeaciones,
        'mes_seleccionado': mes or '',
        'meses': meses,
    }

    return render(request, 'planeaciones/lista_planeaciones.html', context)



 

@login_required
def registrar_planeacion(request):
    if request.method == 'POST':
        form = PlaneacionForm(request.POST, request.FILES)
        if form.is_valid():
            planeacion = form.save(commit=False)
            planeacion.madre = request.user

           # Validación: impedir 2 planeaciones el mismo día
            if Planeacion.objects.filter(madre=request.user, fecha=planeacion.fecha).exists():
                messages.error(request, "❌ Ya existe una planeación registrada para esta fecha.")
                return redirect('planeaciones:registrar_planeacion')

            planeacion.save()
            form.save_m2m()

            # Guardar múltiples imágenes
            for f in request.FILES.getlist('imagenes'):
                Documentacion.objects.create(planeacion=planeacion, imagen=f)

            messages.success(request, '✅ Planeación registrada exitosamente.')
            return redirect('planeaciones:lista_planeaciones')
        else:
            messages.error(request, '❌ Error al registrar la planeación.')
    else:
        form = PlaneacionForm()

    return render(request, 'planeaciones/registrar_planeacion.html', {'form': form})


@login_required
def editar_planeacion(request, id):
    planeacion = get_object_or_404(Planeacion, pk=id)
    documentos = Documentacion.objects.filter(planeacion=planeacion)

    form = PlaneacionForm(request.POST or None, request.FILES or None, instance=planeacion)
    if request.method == 'POST':
        form = PlaneacionForm(request.POST, request.FILES, instance=planeacion)

        # Si el usuario marcó imágenes para eliminar
        eliminar_ids = request.POST.getlist('eliminar_documentos')
        for doc_id in eliminar_ids:
            doc = Documentacion.objects.filter(id=doc_id, planeacion=planeacion).first()
            if doc:
                doc.imagen.delete(save=False)
                doc.delete()

        if form.is_valid():
            planeacion = form.save(commit=False)  # importante para save_m2m
            planeacion.save()
            form.save_m2m()

            # Si subió nuevas imágenes
            for f in request.FILES.getlist('imagenes'):
                Documentacion.objects.create(planeacion=planeacion, imagen=f)

            messages.success(request, 'Planeación actualizada correctamente.')
            return redirect('planeaciones:detalle_planeacion', id=planeacion.id)
        else:
            messages.error(request, 'Ocurrió un error al actualizar la planeación.')
    else:
        form = PlaneacionForm(instance=planeacion)

    return render(request, 'planeaciones/editar_planeacion.html', {
        'form': form,
        'planeacion': planeacion,
        'documentos': documentos
    })

@login_required
def detalle_planeacion(request, id):
    planeacion = get_object_or_404(Planeacion, id=id, madre=request.user)
    documentos = planeacion.documentos.all()
    return render(request, 'planeaciones/detalle_planeacion.html', {
        'planeacion': planeacion,
        'documentos': documentos
    })




@login_required
def eliminar_planeacion(request, id):
    planeacion = get_object_or_404(Planeacion, id=id, madre=request.user)
    if request.method == 'POST':
        planeacion.delete()
        return redirect('planeaciones:lista_planeaciones')
    return render(request, 'planeaciones/eliminar_planeacion.html', {'planeacion': planeacion})

# Función genérica para generar PDF desde HTML
def generar_pdf(template_path, context):
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=reporte.pdf"

    pisa_status = pisa.CreatePDF(html, dest=response, encoding='UTF-8')
    if pisa_status.err:
        return HttpResponse("Error al generar PDF")
    return response


# --- REPORTES ---
@login_required
def reporte_planeacion_pdf(request, id):
    """Reporte individual de una planeación"""
    planeacion = get_object_or_404(Planeacion, id=id, madre=request.user)

    context = {
        "planeacion": planeacion,
        "imagenes": planeacion.documentos.all(),
        "BASE_URL": request.build_absolute_uri('/'),
    }
    template_path = "planeaciones/reporte_individual.html"  # tu template individual
    return generar_pdf(template_path, context)


@login_required
def reporte_todas_pdf(request):
    madre = request.user
    planeaciones = Planeacion.objects.filter(madre=madre).order_by('-fecha')

    # Construir rutas absolutas de imágenes
    for p in planeaciones:
        p.docs = []
        for img in p.documentos.all():
            p.docs.append(request.build_absolute_uri(img.imagen.url))

    context = {
        "planeaciones": planeaciones,
        "BASE_URL": request.build_absolute_uri('/'),
    }

    template_path = "planeaciones/reporte_todas.html"
    return generar_pdf(template_path, context)


@login_required
def reporte_mes_pdf(request):
    madre = request.user
    mes = request.GET.get("mes")

    planeaciones = Planeacion.objects.filter(madre=madre)
    if mes:
        planeaciones = planeaciones.filter(fecha__month=mes)

    planeaciones = planeaciones.order_by('-fecha')

    # Construir rutas absolutas de imágenes
    for p in planeaciones:
        p.docs = []
        for img in p.documentos.all():
            p.docs.append(request.build_absolute_uri(img.imagen.url))

    context = {
        "planeaciones": planeaciones,
        "mes": mes,
        "BASE_URL": request.build_absolute_uri('/'),
    }

    template_path = "planeaciones/reporte_todas.html"
    return generar_pdf(template_path, context)


@login_required
def reporte_menu(request):
    """Menu de selección de reportes"""
    planeaciones = Planeacion.objects.filter(madre=request.user).order_by('-fecha')
    return render(request, 'planeaciones/reporte_menu.html', {
        "planeaciones": planeaciones
    })
@login_required
def eliminar_masivo(request):
    if request.method == 'POST':
        ids = request.POST.getlist('planeaciones_ids')

        if ids:
            Planeacion.objects.filter(id__in=ids).delete()
            messages.success(request, "Planeaciones eliminadas correctamente.")
        else:
            messages.warning(request, "No seleccionaste ninguna planeación.")

    return redirect('planeaciones:lista_planeaciones')

