from django import forms
from .models import Student

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'phone_number', 'parent_phone_number', 'governorate', 'grade', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            qs = Student.objects.filter(phone_number=phone)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('رقم الهاتف مستخدم بالفعل.')
        return phone

    def clean_parent_phone_number(self):
        parent = self.cleaned_data.get('parent_phone_number')
        if parent:
            qs = Student.objects.filter(parent_phone_number=parent)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('رقم ولي الأمر مستخدم بالفعل.')
        return parent

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get("phone_number")
        parent = cleaned_data.get("parent_phone_number")

        # منع تساوي رقم الطالب مع رقم ولي الأمر
        if phone and parent and phone == parent:
            raise forms.ValidationError("رقم الهاتف لا يمكن أن يساوي رقم هاتف ولي الأمر.")

        return cleaned_data


