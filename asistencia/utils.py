from core.models import Asistencia
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType

def verificar_ausencias(nino, usuario, umbral=3):
    ausencias = Asistencia.objects.filter(nino=nino, estado="Ausente").count()

    if ausencias > umbral:
        ya_notificado = Notification.objects.filter(
            title__icontains=f"Ausencias críticas: {nino}",
            level="grave",
            read=False,
            recipient=usuario
        ).exists()

        if not ya_notificado:
            Notification.objects.create(
                title=f"Ausencias críticas: {nino}",
                message=f"{nino} ha faltado {ausencias} veces.",
                level="grave",
                recipient=usuario,  # 🔔 ahora sí se asigna
                content_type=ContentType.objects.get_for_model(nino),
                object_id=nino.id
            )
