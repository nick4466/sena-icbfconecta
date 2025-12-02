from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMessage, get_connection
from django.conf import settings

from core.models import Padre, MadreComunitaria
from .forms import EmailMassForm
from .models import ArchivoAdjunto, EmailLog
from django.views.decorators.http import require_POST
from django.db.models import Q
from datetime import datetime


def obtener_choices_padres(madre):
    """
    Retorna una lista de tuplas (id_padre, "Nombre del padre - Nombres de los niños")
    solo de los padres asociados a los hogares de la madre comunitaria.
    """
    # Obtenemos los IDs de los hogares asignados a la madre
    hogares_ids = madre.hogares_asignados.values_list("id", flat=True)

    # Obtenemos los padres que tienen niños en esos hogares
    padres = Padre.objects.filter(
        ninos__hogar_id__in=hogares_ids
    ).distinct().select_related("usuario")

    choices = []
    for padre in padres:
        # Obtenemos los nombres de todos los niños asociados a ese padre en esos hogares
        ninos = padre.ninos.filter(hogar_id__in=hogares_ids)
        nombres_ninos = ", ".join([f"{n.nombres} {n.apellidos}" for n in ninos])

        # Formamos la cadena "Nombre del padre - Nombres de los niños"
        label = f"{padre.usuario.nombres} {padre.usuario.apellidos} - {nombres_ninos}"
        choices.append((padre.id, label))

    return choices

def enviar_correos(request):

    # =============================
    # 1. OBTENER LA MADRE LOGUEADA
    # =============================
    try:
        madre = request.user.madre_profile
    except MadreComunitaria.DoesNotExist:
        messages.error(request, "Solo las Madres Comunitarias pueden enviar correos.")
        return redirect("home")

    # Hogares asignados a esa madre
    hogares_ids = madre.hogares_asignados.values_list("id", flat=True)

    # =============================
    # 2. GET → crear formulario filtrado
    # =============================
    if request.method == "GET":
        form = EmailMassForm(destinatarios_choices=obtener_choices_padres(madre))
        return render(request, "correos/enviar.html", {"form": form})

    # =============================
    # 3. POST → procesar formulario
    # =============================
    form = EmailMassForm(request.POST, request.FILES, destinatarios_choices=obtener_choices_padres(madre))

    if not form.is_valid():
        return render(request, "correos/enviar.html", {"form": form})

    selected_ids = form.cleaned_data['destinatarios']
    asunto = form.cleaned_data['asunto']
    cuerpo = form.cleaned_data['cuerpo']
    archivos = request.FILES.getlist('archivos')

    # =============================
    # 4. FILTRO SEGURO DE PADRES
    # =============================
    padres = Padre.objects.filter(
        id__in=selected_ids,
        ninos__hogar_id__in=hogares_ids
    ).distinct().select_related("usuario").prefetch_related("ninos")

    # Si por manipulación un padre no pertenece a la madre → no se permite
    if not padres.exists():
        messages.error(request, "No tienes permiso para contactar a esos padres.")
        return redirect("correos:enviar")

    # =============================
    # 5. Guardar adjuntos
    # =============================
    adjuntos_guardados = []
    for f in archivos:
        adj = ArchivoAdjunto(archivo=f, nombre_original=f.name)
        adj.save()
        adjuntos_guardados.append(adj)

    # Construir lista de destinatarios con información legible (padre - niños <email>)
    destinatarios_lista = []
    for p in padres:
        correo = p.usuario.correo
        nombres_ninos = ", ".join([f"{n.nombres} {n.apellidos}" for n in p.ninos.all()])
        label = f"{p.usuario.nombres} {p.usuario.apellidos} - {nombres_ninos} <{correo}>"
        destinatarios_lista.append(label)

    connection = get_connection()
    try:
        connection.open()
    except:
        pass

    fallos = []

    for p in padres:
        correo_padre = p.usuario.correo
        nombres_ninos = ", ".join([f"{n.nombres} {n.apellidos}" for n in p.ninos.all()])

        cuerpo_final = (
            f"Hola {p.usuario.nombres},\n\n"
            f"{cuerpo}\n\n"
            f"Niño(s) asociado(s): {nombres_ninos}"
        )

        email = EmailMessage(
            subject=asunto,
            body=cuerpo_final,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[correo_padre],
            connection=connection
        )

        for adj in adjuntos_guardados:
            email.attach(adj.nombre_original, adj.archivo.read())

        try:
            email.send()
        except Exception as e:
            fallos.append(f"{correo_padre}: {str(e)}")

    # =============================
    # 6. Guardar Log
    # =============================
    # Guardamos los destinatarios como una cadena separada por '||' para preservar comas
    log = EmailLog.objects.create(
        asunto=asunto,
        cuerpo=cuerpo,
        destinatarios="||".join(destinatarios_lista),
        enviado_con_exito=(len(fallos) == 0),
        nota_error="\n".join(fallos)
    )

    if adjuntos_guardados:
        log.adjuntos.set(adjuntos_guardados)

    messages.success(request, "Correos enviados correctamente.")
    return redirect("correos:historial")



def historial(request):
    logs = EmailLog.objects.all().order_by("-fecha_envio")

    # --- FILTROS ---
    mes = request.GET.get("mes")
    nombre = request.GET.get("nombre")

    # Filtrar por mes
    if mes:
        try:
            fecha = datetime.strptime(mes, "%Y-%m")
            logs = logs.filter(
                fecha_envio__year=fecha.year,
                fecha_envio__month=fecha.month
            )
        except:
            pass

    # Filtrar por nombre de destinatario (correo)
    if nombre:
        logs = logs.filter(destinatarios__icontains=nombre)

    # Lista de correos convertida en array
    for log in logs:
        labels = []
        raw = log.destinatarios or ""

        # Soportar ambos formatos: nuevo '||' y antiguo separado por comas
        if '||' in raw:
            parts = [p.strip() for p in raw.split('||') if p.strip()]
        else:
            parts = [p.strip() for p in raw.split(',') if p.strip()]

        for part in parts:
            text = part
            # Si viene como 'Nombre - Niños <email>' eliminar el email
            if '<' in text and '>' in text:
                text = text.split('<')[0].strip()

            # Si lo que queda es un correo (ej. registros antiguos), intentar resolver el padre
            if '@' in text and not any(c.isalpha() for c in text.replace('@', '')):
                # es muy probablemente un email
                try:
                    padre = Padre.objects.select_related('usuario').prefetch_related('ninos').get(usuario__correo__iexact=text)
                    ninos = ", ".join([f"{n.nombres} {n.apellidos}" for n in padre.ninos.all()])
                    label = f"{padre.usuario.nombres} {padre.usuario.apellidos} - {ninos}" if ninos else f"{padre.usuario.nombres} {padre.usuario.apellidos}"
                    labels.append(label)
                except Padre.DoesNotExist:
                    labels.append(text)
            else:
                # ya es una etiqueta con nombres → añadir tal cual
                labels.append(text)

        log.lista_destinatarios = labels

    return render(request, "correos/historial.html", {
        "logs": logs
    })
@require_POST
def eliminar_log(request, log_id):
    try:
        log = EmailLog.objects.get(id=log_id)
        log.delete()
        messages.success(request, "Registro eliminado correctamente.")
    except EmailLog.DoesNotExist:
        messages.error(request, "El registro no existe.")
    return redirect("correos:historial")


@require_POST
def vaciar_historial(request):
    EmailLog.objects.all().delete()
    messages.success(request, "Historial vaciado correctamente.")
    return redirect("correos:historial")
