from django import forms
from .models import Student

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'parent_phone_number', 'governorate', 'grade', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_parent_phone_number(self):
        parent = self.cleaned_data.get('parent_phone_number')
        if parent:
            qs = Student.objects.filter(parent_phone_number=parent)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('رقم هاتف ولي الأمر مستخدم بالفعل.')
        return parent
