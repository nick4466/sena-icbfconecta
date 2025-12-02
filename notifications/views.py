from django.shortcuts import render
# Create your views here.
from django.http import JsonResponse
from .models import Notification
from django.contrib.auth.decorators import login_required

@login_required
def marcar_todo_leido(request):
    if request.method == "POST":
        Notification.objects.filter(recipient=request.user, read=False).update(read=True)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@login_required
def notificaciones_list(request):
    # Filtrar solo las notificaciones del usuario logueado
    notificaciones = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    return render(request, 'notificaciones/list.html', {
        'notificaciones': notificaciones
    })
