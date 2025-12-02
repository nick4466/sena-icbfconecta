from django import forms
from django.contrib.auth.forms import PasswordResetForm
from core.models import Usuario
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Correo electrónico", max_length=254)

    def get_users(self, email):
        active_users = Usuario._default_manager.filter(correo__iexact=email, is_active=True)
        print("🔍 Usuarios encontrados:", active_users)
        return (u for u in active_users if u.has_usable_password())

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # 💡 CORRECCIÓN: Convertir el generador a una lista inmediatamente.
        # Esto evita que se "gaste" al ser verificado y luego usado en el método save().
        self.users_cache = list(self.get_users(email))
        
        if not self.users_cache:
            raise forms.ValidationError("No existe un usuario activo con ese correo.")
        return email

    def save(self, domain_override=None,
             subject_template_name='password_reset/password_reset_subject.txt',
             email_template_name='password_reset/password_reset_email.html',
             use_https=False, token_generator=None,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):

        email = self.cleaned_data["email"]
        users = list(self.get_users(email))

        print("📨 Backend activo:", settings.EMAIL_BACKEND)
        print("📧 EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)
        print("📧 EMAIL_HOST_PASSWORD:", "✅ cargada" if settings.EMAIL_HOST_PASSWORD else "❌ vacía")

        if not users:
            print("⚠️ No se encontraron usuarios activos con ese correo.")
            return

        try:
            # Llamar al método original de PasswordResetForm (gestiona tokens y plantillas)
            super().save(domain_override, subject_template_name, email_template_name,
                         use_https, token_generator, from_email or settings.DEFAULT_FROM_EMAIL,
                         request, html_email_template_name, extra_email_context)
            print("✅ Correo de restablecimiento enviado (si usas SMTP, debería llegar al buzón).")
        except Exception as e:
            print("❌ Error al enviar el correo de restablecimiento:", str(e))
            raise forms.ValidationError(f"Error al enviar el correo: {e}")
