from django import forms
from .models import Planeacion, Documentacion, Dimension

class PlaneacionForm(forms.ModelForm):

    dimensiones = forms.ModelMultipleChoiceField(
        queryset=Dimension.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Dimensiones trabajadas"
    )

    class Meta:
        model = Planeacion
        exclude = ['madre']
        widgets = {
            'fecha': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date',
                       'placeholder': 'Selecciona una fecha'}
            ),
            'nombre_experiencia': forms.TextInput(
                attrs={
                    'placeholder': 'Nombre de la Planeación Pedagógica'
                }
            ),
            'intencionalidad_pedagogica': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Describe el propósito de la planeación pedagógica'
                }
            ),
            'materiales_utilizar': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Materiales necesarios para las actividades'
                }
            ),
            'ambiente_educativo': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '¿Cómo vas a ambientar el aula o espacio educativo?'
                }
            ),
            'experiencia_inicio': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Describe el inicio de la experiencia'
                }
            ),
            'experiencia_pedagogica': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Describe el desarrollo de la experiencia pedagógica'
                }
            ),
            'cierre_experiencia': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': '¿Cómo finaliza la actividad?'
                }
            ),
            'situaciones_presentadas': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Observaciones y situaciones presentadas'
                }
            ),
        }
        labels = {
            'nombre_experiencia': 'Nombre de la experiencia',
            'intencionalidad_pedagogica': 'Intencionalidad pedagógica',
            'materiales_utilizar': 'Materiales a utilizar',
            'ambiente_educativo': 'Decoración o ambientación del espacio educativo',
            'experiencia_inicio': 'Inicio de la experiencia',
            'experiencia_pedagogica': 'Desarrollo de la experiencia pedagógica',
            'cierre_experiencia': 'Cierre de la experiencia',
            'situaciones_presentadas': 'Seguimiento de situaciones presentadas',
        }


class DocumentacionForm(forms.ModelForm):
    class Meta:
        model = Documentacion
        fields = ['imagen']
