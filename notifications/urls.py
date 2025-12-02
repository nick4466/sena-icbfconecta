from django.urls import path
from . import views

urlpatterns = [
    path('marcar-todo-leido/', views.marcar_todo_leido, name='marcar_todo_leido'),
]
