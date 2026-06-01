from django.contrib.auth.forms import UserCreationForm
from django import forms
import re
from django.core.exceptions import ValidationError
from authentication.models import User, Role
from .models import SupervisorProfile, StudentProfile, AssociationProfile, CoordinatorProfile
from .widgets import SupervisorSearchWidget

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

    def __init__(self, *args, request=None, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        self.instructions = (
            "Note that by signing up here, you will be registering as a student. If you have any questions, contact astrolink@siriusa.nl"
        )

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

class AdminSignUpForm(SignUpForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.exclude(name="Own Data").exclude(name="External User")
    )

class SupervisorSignUpForm(SignUpForm):
    class Meta(SignUpForm.Meta):
        model = User
        fields = SignUpForm.Meta.fields  # same fields as regular signup

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Instructions for pending approval
        self.instructions = (
            "By signing up as a supervisor, your account will be created but will require approval "
            "by an administrator before you can log in."
        )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "screen_name",
            "phone_number",
        ]

class SupervisorProfileForm(forms.ModelForm):
    academic_supervisor = forms.ModelChoiceField(queryset=SupervisorProfile.objects.none(), required=False, widget=SupervisorSearchWidget())
    
    class Meta:
        model = SupervisorProfile
        fields = ["biography", "pnumber", "profile_picture", "academic_supervisor"]
        help_texts = {
            "academic_supervisor": (
                "If you are a PhD student, select your academic supervisor. "
                "Leave empty if you are an independent supervisor."
            )
        }
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["academic_supervisor"].queryset = (
                SupervisorProfile.objects
                .filter(
                    academic_supervisor__isnull=True
                )
                .exclude(pk=self.instance.pk)
                .select_related("user")
            )

    def clean_academic_supervisor(self):
        supervisor = self.cleaned_data.get("academic_supervisor")

        if supervisor is None:
            return None

        if supervisor.is_phd_student():
            raise forms.ValidationError(
                "You cannot select a PhD student as your academic supervisor."
            )

        return supervisor


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["biography", "study_programme", "level", "snumber"]

class AssociationProfileForm(forms.ModelForm):
    class Meta:
        model = AssociationProfile
        fields = ["biography", "website", "profile_picture"]

class CoordinatorProfileForm(forms.ModelForm):
    class Meta:
        model = CoordinatorProfile
        fields = ["study_programme", "level"]