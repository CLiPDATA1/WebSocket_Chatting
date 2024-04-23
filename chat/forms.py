# chat > forms.py

from django import forms
from .models import CustomUser

class SignupForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'dept_code', 'site_code']
        widgets = {
            'password': forms.PasswordInput()
        }