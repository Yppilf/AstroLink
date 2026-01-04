from django.contrib.auth.forms import UserCreationForm
from django import forms
import re
from django.core.exceptions import ValidationError
from authentication.models import User

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class SignUpForm(UserCreationForm):
    # Data fields
    email = forms.EmailField()
    first_name = forms.CharField(label="First Name", max_length=255)
    last_name = forms.CharField(label="Last Name", max_length=255)
    phone_number = forms.CharField(label="Phone Number", max_length=255)

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'password1',
            'password2',
        ]

    def clean_email(self):
        email = self.cleaned_data['email']
        regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        if not re.fullmatch(regex, email):
            raise forms.ValidationError("Please enter a valid email address.")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not re.match(r'^[^\W\d_][\w\s\-]*$', first_name):
            raise forms.ValidationError("First Name must contain only letters, spaces, or dashes.")
        if len(first_name) < 1:
            raise forms.ValidationError("First Name must not be empty.")
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not re.match(r'^[^\W\d_][\w\s\-]*$', last_name):
            raise forms.ValidationError("Last Name must contain only letters, spaces, or dashes.")
        if len(last_name) < 1:
            raise forms.ValidationError("Last Name must not be empty.")
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if phone_number:
            if not re.match(r'^\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$', phone_number):
                raise ValidationError("Enter a valid phone number.")
        return phone_number
   
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        if commit:
            user.save()
        return user
