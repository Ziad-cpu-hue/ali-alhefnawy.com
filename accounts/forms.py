from django import forms
from .models import Student

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'phone_number', 'parent_phone_number', 'governorate', 'grade', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

