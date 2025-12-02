from django import forms
from .models import Novedad
from core.models import Nino

class NovedadForm(forms.ModelForm):
    nino = forms.ModelChoiceField(queryset=Nino.objects.none())
    class Meta:
        model = Novedad
        exclude = ['docente']
        fields = [
            'nino',
            'fecha',
            'clase',
            'tipo',
            'docente',
            'descripcion',
            'causa',
            'disposicion',
            'acuerdos',
            'observaciones',
            'archivo_pdf',

        ]
        widgets = {
            'tipo': forms.Select(),
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

