# chat > forms.py

from django import forms
from .models import CustomUser

class SignupForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'user_type']
        widgets = {
            'password': forms.PasswordInput()
        }