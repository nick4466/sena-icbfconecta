from django import forms

class EmailMassForm(forms.Form):
    destinatarios = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple
    )
    asunto = forms.CharField(max_length=255)
    
    cuerpo = forms.CharField(widget=forms.Textarea)
    

    def __init__(self, *args, destinatarios_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if destinatarios_choices:
            self.fields['destinatarios'].choices = destinatarios_choices
