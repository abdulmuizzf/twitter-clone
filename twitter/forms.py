from django import forms
from django.core.exceptions import ValidationError
from django import forms
from django.forms import widgets
from .validators import UsernameValidator
from .models import User

def unique_username_validator(username):
    if User.objects.filter(username=username).exists():
        raise ValidationError("Username already exists")
    return username

class SignupForm(forms.Form):
    display_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control',
                                                            'placeholder': 'Display Name'}),
                                label='',
                                max_length=80)
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control',
                                                            'placeholder': 'Username'}),
                                label='',
                                max_length=50, 
                                validators=[UsernameValidator(), unique_username_validator])
    bio = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control',
                                        'cols': '20', 'rows': '2',
                                        'placeholder': 'Bio'}),
                        label='',
                        max_length=160)   
