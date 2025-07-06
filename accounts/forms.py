from django import forms
from .models import Student

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'phone_number', 'parent_phone_number', 'governorate', 'grade', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

###########################################################################

from django import forms
from .models import PaymentRequest

INPUT_CLASS = "rounded-xl bg-[#21284a] h-14 px-4 placeholder:text-[#8e99cc] focus:outline-none w-full"

class FullPaymentForm(forms.ModelForm):
    class Meta:
        model = PaymentRequest
        fields = [
            'course',
            'sender_phone',
            'recipient_phone',
            'txn_id',
            'screenshot',
        ]
        widgets = {
            'course': forms.HiddenInput(),
            'sender_phone': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'رقم الهاتف المرسل'
            }),
            'recipient_phone': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'رقم الهاتف المستلم'
            }),
            'txn_id': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'رقم المعاملة'
            }),
            'screenshot': forms.ClearableFileInput(attrs={
                'class': "w-full"
            }),
        }
