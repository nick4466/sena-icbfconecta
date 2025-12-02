from django import forms
from core.models import Asistencia  # Asegúrate de tener este modelo

class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = '__all__'  # O especifica los campos que quieres usar
