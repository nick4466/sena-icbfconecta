# core/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from .models import Usuario, Nino, MadreComunitaria, HogarComunitario, Regional, Ciudad, Discapacidad


# ----------------------------------------------------
# 🟩 FORMULARIO DE LOGIN PERSONALIZADO
# ----------------------------------------------------
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate


from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario, Nino, MadreComunitaria, HogarComunitario, Regional # Asegúrate de importar estos modelos
# ... (resto de tus imports)

# --- Formulario de Usuario para la Madre Comunitaria ---
class UsuarioMadreForm(forms.ModelForm):
    # Campos requeridos para la autenticación y base del Usuario
    documento = forms.IntegerField(label='Número de Documento', required=True)
    correo = forms.EmailField(label="Correo electrónico", required=True)
    nombres = forms.CharField(label="Nombres", max_length=50, required=True)
    apellidos = forms.CharField(label="Apellidos", max_length=50, required=True)
    
    class Meta:
        model = Usuario
        # Incluye todos los campos de Usuario que necesitas para el registro
        fields = ['documento', 'tipo_documento', 'nombres', 'apellidos', 'correo', 'telefono', 'direccion']

# --- Formulario del Perfil MadreComunitaria ---
class MadreProfileForm(forms.ModelForm):
    foto_madre = forms.ImageField(label="Foto de la Madre", required=True, widget=forms.FileInput(attrs={'accept': 'image/*'}))

    class Meta:
        model = MadreComunitaria
        # Incluye todos los campos del perfil de la madre
        exclude = ['usuario', 'fecha_registro']
        widgets = {
             # Es crucial listar todos los FileField aquí
             'foto_madre': forms.FileInput(),
             'firma_digital': forms.FileInput(),
             'documento_identidad_pdf': forms.FileInput(),
             'certificado_escolaridad_pdf': forms.FileInput(),
             'certificado_antecedentes_pdf': forms.FileInput(),
             'certificado_medico_pdf': forms.FileInput(),
             'certificado_residencia_pdf': forms.FileInput(),
             'cartas_recomendacion_pdf': forms.FileInput(),
        }

# --- Formulario de Hogar Comunitario ---
class HogarForm(forms.ModelForm):
    regional = forms.ModelChoiceField(
        queryset=Regional.objects.all(),
        required=True,
        label="Regional",
        widget=forms.Select,
        empty_label="-- Seleccione una Regional --"
    )
    ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        required=True,
        label="Ciudad",
        widget=forms.Select,
        empty_label="-- Seleccione una Ciudad --"
    )

    class Meta:
        model = HogarComunitario
        fields = ['regional', 'ciudad', 'direccion', 'localidad']  # Ajusta según los campos reales del modelo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'regional' in self.data:
            try:
                regional_id = int(self.data.get('regional'))
                self.fields['ciudad'].queryset = Ciudad.objects.filter(regional_id=regional_id).order_by('nombre')
            except (ValueError, TypeError):
                self.fields['ciudad'].queryset = Ciudad.objects.none()
        elif self.instance and self.instance.pk and self.instance.regional:
            self.fields['ciudad'].queryset = Ciudad.objects.filter(regional=self.instance.regional).order_by('nombre')
        else:
            self.fields['ciudad'].queryset = Ciudad.objects.none()

# ----------------------------------------------------
# 💡 NUEVO: Formulario para Administradores
# ----------------------------------------------------
class AdminForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput, required=False, label="Nueva Contraseña")
    foto_admin = forms.ImageField(label="Foto de Perfil", required=False, widget=forms.FileInput(attrs={'accept': 'image/*'}))

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'documento', 'correo', 'foto_admin', 'contraseña']


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(
        label='Número de Documento',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su número de documento',
            'autofocus': True
        })
    )

    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )


# ----------------------------------------------------
# 🟩 FORMULARIO DE RESETEO DE CONTRASEÑA
# ----------------------------------------------------
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )

    def clean_email(self):
        """
        Valida que el correo electrónico exista en la base de datos para un usuario activo.
        """
        email = self.cleaned_data.get("email")
        # Usamos list() para ejecutar la consulta y ver si hay resultados.
        if not list(self.get_users(email)):
            raise forms.ValidationError("No existe un usuario activo registrado con ese correo electrónico.")
        return email

    def get_users(self, email):
        """
        Sobrescribimos este método porque nuestro modelo Usuario usa 'correo' en lugar de 'email'.
        Busca usuarios activos que coincidan con el correo proporcionado.
        """
        active_users = Usuario._default_manager.filter(correo__iexact=email, is_active=True)
        return (u for u in active_users if u.has_usable_password())


# ----------------------------------------------------
# 💡 FORMULARIOS DE PERFIL
# ----------------------------------------------------
class AdminPerfilForm(forms.ModelForm):
    """Formulario para que el Administrador edite su perfil."""
    correo = forms.EmailField(label="Correo electrónico", required=True)
    foto_admin = forms.ImageField(label="Foto de Perfil", required=False, widget=forms.FileInput(attrs={'accept': 'image/*'}))

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'correo', 'foto_admin']


class MadrePerfilForm(forms.ModelForm):
    """Formulario para que la Madre Comunitaria edite su perfil."""
    correo = forms.EmailField(label="Correo electrónico", required=True)

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'correo', 'telefono', 'direccion']
        widgets = {
            'nombres': forms.TextInput(attrs={'required': True}),
            'apellidos': forms.TextInput(attrs={'required': True}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej. 3001234567'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Ej. Calle 10 #5-25'}),
        }


class PadrePerfilForm(forms.ModelForm):
    """Formulario para que el Padre de Familia edite su perfil."""
    correo = forms.EmailField(label="Correo electrónico", required=True)
    ocupacion = forms.CharField(max_length=50, required=False)

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'correo', 'telefono', 'direccion']
        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej. 3112223344'}),
        }


# ----------------------------------------------------
# 👶 FORMULARIO DE NIÑOS (Expandido)
# ----------------------------------------------------
class NinoForm(forms.ModelForm):
    foto = forms.ImageField(
        label="Foto del Niño",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )
    carnet_vacunacion = forms.FileField(
        label="Carné de Vacunación",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*,application/pdf'})
    )
    certificado_eps = forms.FileField(
        label="Certificado EPS/Afiliación",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*,application/pdf'})
    )
    registro_civil_img = forms.FileField(
        label="Foto Registro Civil",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*,application/pdf'})
    )
    otro_pais = forms.CharField(
        label="Especifique otro país",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Escriba el país de nacimiento...'})
    )
    tipo_sangre = forms.ChoiceField(
        choices=Nino.TIPO_SANGRE_CHOICES,
        label="Tipo de Sangre",
        required=False
    )
    parentesco = forms.ChoiceField(
        choices=Nino.PARENTESCO_CHOICES,
        label="Parentesco con el Niño",
        required=True
    )
    tiene_discapacidad = forms.BooleanField(
        label="¿Tiene alguna discapacidad?",
        required=False
    )
    tipos_discapacidad = forms.ModelMultipleChoiceField(
        queryset=Discapacidad.objects.all(),
        label="Tipo(s) de Discapacidad",
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    otra_discapacidad = forms.CharField(
        label="Otra discapacidad (especifique)",
        required=False
    )

    class Meta:
        model = Nino
        fields = [
            'nombres', 'apellidos', 'documento', 'fecha_nacimiento', 'genero', 'nacionalidad', 'otro_pais',
            'tipo_sangre', 'parentesco', 'tiene_discapacidad', 'tipos_discapacidad', 'otra_discapacidad',
            'foto', 'carnet_vacunacion', 'certificado_eps', 'registro_civil_img'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'nacionalidad': forms.Select(attrs={'class': 'nacionalidad-select'}),
        }
        labels = {
            'nacionalidad': '¿En qué país nació?',
        }

    def clean(self):
        cleaned_data = super().clean()
        tiene_discapacidad = cleaned_data.get('tiene_discapacidad')
        tipos_discapacidad = cleaned_data.get('tipos_discapacidad')
        otra_discapacidad = cleaned_data.get('otra_discapacidad')
        nacionalidad = cleaned_data.get('nacionalidad')
        otro_pais = cleaned_data.get('otro_pais')
        fecha_nacimiento = cleaned_data.get('fecha_nacimiento')
        
        # Validar edad del niño (debe estar entre 1 y 5 años)
        if fecha_nacimiento:
            from datetime import date
            hoy = date.today()
            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            
            if edad < 1:
                self.add_error('fecha_nacimiento', 'El niño tiene menos de 1 año y no puede ser matriculado. La edad mínima es de 1 año.')
            elif edad > 5:
                self.add_error('fecha_nacimiento', 'El niño es mayor de 5 años y no puede ser matriculado. La edad máxima es de 5 años.')
        
        if tiene_discapacidad:
            if not tipos_discapacidad and not otra_discapacidad:
                self.add_error('tipos_discapacidad', 'Seleccione al menos un tipo de discapacidad o especifique otra.')
                
        # Validar que si selecciona "otro" país, debe especificarlo
        if nacionalidad == 'otro' and not otro_pais:
            self.add_error('otro_pais', 'Debe especificar el país cuando selecciona "Otro país".')
            
        return cleaned_data


# ----------------------------------------------------
# 👨 FORMULARIO DE REGISTRO DE PADRES (Expandido)
# ----------------------------------------------------
class PadreForm(forms.ModelForm):
    # Campos de Usuario
    documento = forms.IntegerField(label='Número de Documento', required=True)
    nombres = forms.CharField(max_length=50, label="Nombres", required=True)
    apellidos = forms.CharField(max_length=50, label="Apellidos", required=True)
    correo = forms.EmailField(label="Correo electrónico", required=True)
    tipo_documento = forms.ChoiceField(
        choices=[('CC', 'Cédula de ciudadanía'), ('TI', 'Tarjeta de identidad'), ('CE', 'Cédula de extranjería'), ('PA', 'Pasaporte')],
        label="Tipo de Documento",
        required=True
    )
    telefono = forms.CharField(max_length=20, label="Teléfono", required=True)
    direccion = forms.CharField(max_length=100, label="Dirección", required=False)
    
    # Campos de Padre (perfil)
    OCUPACION_CHOICES = [
        ('', '-- Seleccione una ocupación --'),
        ('empleado_publico', 'Empleado Público'),
        ('empleado_privado', 'Empleado Privado'),
        ('independiente', 'Trabajador Independiente'),
        ('comerciante', 'Comerciante'),
        ('agricultor', 'Agricultor'),
        ('constructor', 'Constructor/Albañil'),
        ('conductor', 'Conductor'),
        ('docente', 'Docente/Educador'),
        ('salud', 'Profesional de la Salud'),
        ('servicios', 'Servicios (Limpieza, Seguridad, etc.)'),
        ('domestico', 'Trabajador Doméstico'),
        ('estudiante', 'Estudiante'),
        ('pensionado', 'Pensionado'),
        ('desempleado', 'Desempleado'),
        ('ama_casa', 'Ama de Casa'),
        ('vendedor', 'Vendedor'),
        ('mecanico', 'Mecánico'),
        ('artesano', 'Artesano'),
        ('otro', 'Otro')
    ]
    
    ocupacion = forms.ChoiceField(
        choices=OCUPACION_CHOICES,
        label="Ocupación",
        required=True,
        widget=forms.Select(attrs={'class': 'ocupacion-select'})
    )
    otra_ocupacion = forms.CharField(
        max_length=50, 
        required=False, 
        label="Especifique otra ocupación",
        widget=forms.TextInput(attrs={'placeholder': 'Escriba la ocupación...'})
    )
    estrato = forms.IntegerField(
        label="Estrato",
        required=False,
        min_value=1,
        max_value=6,
        widget=forms.NumberInput(attrs={'min': '1', 'max': '6'})
    )
    telefono_contacto_emergencia = forms.CharField(
        max_length=20,
        label="Teléfono de Contacto de Emergencia",
        required=False
    )
    nombre_contacto_emergencia = forms.CharField(
        max_length=100,
        label="Nombre del Contacto de Emergencia",
        required=False
    )
    situacion_economica_hogar = forms.CharField(
        max_length=100,
        label="Situación Económica del Hogar",
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )
    documento_identidad_img = forms.FileField(
        label="Cédula/Documento de Identidad",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*,application/pdf'})
    )
    clasificacion_sisben = forms.FileField(
        label="Foto Clasificación SISBEN",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*,application/pdf'})
    )

    class Meta:
        model = Usuario
        fields = ['tipo_documento', 'documento', 'nombres', 'apellidos', 'correo', 'telefono', 'direccion']
        widgets = {
            'telefono': forms.TextInput(attrs={'required': True}),
        }

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        documento = self.cleaned_data.get('documento')

        # Si el formulario está ligado a una instancia (edición), el chequeo es diferente
        if self.instance and self.instance.pk:
            if Usuario.objects.filter(correo=correo).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Este correo ya está en uso por otro usuario.')
        # Si es un formulario de creación y el correo ya existe
        elif not self.instance.pk and Usuario.objects.filter(correo=correo).exists():
            raise forms.ValidationError('Este correo ya está registrado. Si es el mismo padre, usa su número de documento para cargarlo.')
        return correo

    def clean(self):
        cleaned_data = super().clean()
        documento = cleaned_data.get('documento')
        ocupacion = cleaned_data.get('ocupacion')
        otra_ocupacion = cleaned_data.get('otra_ocupacion')
        
        if not documento or not str(documento).isdigit():
            self.add_error('documento', 'El documento debe ser un número válido.')
            
        # Validar que si selecciona "otro", debe especificar la ocupación
        if ocupacion == 'otro' and not otra_ocupacion:
            self.add_error('otra_ocupacion', 'Debe especificar la ocupación cuando selecciona "Otro".')
            
        return cleaned_data


# ----------------------------------------------------
# 🆕 NUEVOS FORMULARIOS PARA MEJORAS DE MATRÍCULA
# ----------------------------------------------------

class NinoSoloForm(forms.ModelForm):
    """Formulario solo para el niño cuando se asigna a un padre existente"""
    foto = forms.ImageField(
        label="Foto del Niño",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )
    carnet_vacunacion = forms.FileField(
        label="Carné de Vacunación",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*,application/pdf'})
    )
    certificado_eps = forms.FileField(
        label="Certificado EPS/Afiliación",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*,application/pdf'})
    )
    registro_civil_img = forms.FileField(
        label="Foto Registro Civil",
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*,application/pdf'})
    )
    otro_pais = forms.CharField(
        label="Especifique otro país",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Escriba el país de nacimiento...'})
    )
    tipo_sangre = forms.ChoiceField(
        choices=Nino.TIPO_SANGRE_CHOICES,
        label="Tipo de Sangre",
        required=False
    )
    parentesco = forms.ChoiceField(
        choices=Nino.PARENTESCO_CHOICES,
        label="Parentesco con el Niño",
        required=True
    )
    tiene_discapacidad = forms.BooleanField(
        label="¿Tiene alguna discapacidad?",
        required=False
    )
    tipos_discapacidad = forms.ModelMultipleChoiceField(
        queryset=Discapacidad.objects.all(),
        label="Tipo(s) de Discapacidad",
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    otra_discapacidad = forms.CharField(
        label="Otra discapacidad (especifique)",
        required=False
    )

    class Meta:
        model = Nino
        fields = [
            'nombres', 'apellidos', 'documento', 'fecha_nacimiento', 'genero', 'nacionalidad', 'otro_pais',
            'tipo_sangre', 'parentesco', 'tiene_discapacidad', 'tipos_discapacidad', 'otra_discapacidad',
            'foto', 'carnet_vacunacion', 'certificado_eps', 'registro_civil_img'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'nacionalidad': forms.Select(attrs={'class': 'nacionalidad-select'}),
        }
        labels = {
            'nacionalidad': '¿En qué país nació?',
        }

    def clean(self):
        cleaned_data = super().clean()
        tiene_discapacidad = cleaned_data.get('tiene_discapacidad')
        tipos_discapacidad = cleaned_data.get('tipos_discapacidad')
        otra_discapacidad = cleaned_data.get('otra_discapacidad')
        nacionalidad = cleaned_data.get('nacionalidad')
        otro_pais = cleaned_data.get('otro_pais')
        
        if tiene_discapacidad:
            if not tipos_discapacidad and not otra_discapacidad:
                self.add_error('tipos_discapacidad', 'Seleccione al menos un tipo de discapacidad o especifique otra.')
                
        # Validar que si selecciona "otro" país, debe especificarlo
        if nacionalidad == 'otro' and not otro_pais:
            self.add_error('otro_pais', 'Debe especificar el país cuando selecciona "Otro país".')
            
        return cleaned_data


class BuscarPadreForm(forms.Form):
    """Formulario para buscar un padre por documento"""
    documento = forms.CharField(
        label="Documento del Padre",
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ingrese el documento del padre...',
            'class': 'buscar-padre-documento'
        })
    )
    
    def clean_documento(self):
        documento = self.cleaned_data.get('documento')
        if not documento or not documento.isdigit():
            raise forms.ValidationError('El documento debe ser un número válido.')
        return documento


class CambiarPadreForm(forms.Form):
    """Formulario para seleccionar niño y cambiar su padre"""
    nino = forms.ModelChoiceField(
        queryset=Nino.objects.none(),  # Se configurará dinámicamente
        label="Seleccionar Niño",
        empty_label="-- Seleccione el niño --",
        widget=forms.Select(attrs={'class': 'nino-select'})
    )
    
    def __init__(self, hogar=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hogar:
            self.fields['nino'].queryset = Nino.objects.filter(hogar=hogar).order_by('nombres', 'apellidos')