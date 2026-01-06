from django import forms
from .models import Project, CaseStudy, ResearchGroup, Reference, Application, Company, Interest
from authentication.models import SupervisorProfile
import re

# Helper email validator
def validate_email(value):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    if not re.fullmatch(regex, value):
        raise forms.ValidationError("Please enter a valid email address.")
    return value

class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = ["title", "description", "link"]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        # Pop supervisor from kwargs before passing to ModelForm
        self.supervisor = kwargs.pop("supervisor", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit=False)

        # Always assign supervisor for new objects
        if not obj.pk:
            if self.supervisor is None:
                raise ValueError("Supervisor must be provided to save a new Reference.")
            obj.supervisor = self.supervisor

        if commit:
            obj.save()
        return obj

class InterestForm(forms.ModelForm):
    class Meta:
        model = Interest
        fields = ["topic", "experience"]
        widgets = {
            "experience": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop("student", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit=False)

        if not obj.pk:
            if self.student is None:
                raise ValueError("Student must be provided to save a new Interest.")
            obj.student = self.student

        if commit:
            obj.save()
        return obj

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'time_estimate']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, supervisor=None, **kwargs):
        self.supervisor = supervisor
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit=False)
        # assign supervisor on creation
        if not obj.pk:
            if self.supervisor is None:
                raise ValueError("Supervisor must be provided to save a new Project.")
            obj.supervisor = self.supervisor
        if commit:
            obj.save()
        return obj

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "description",
            "email",
            "contact_name",
            "contact_phone",
            "website",
            "status",
            "logo",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "logo": forms.FileInput(),
        }

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean_email(self):
        return validate_email(self.cleaned_data["email"])

    def save(self, commit=True):
        obj = super().save(commit=False)

        # Only set association on CREATE
        if obj.pk is None:
            if not self.request or not hasattr(self.request.user, "associationprofile"):
                raise ValueError("Association user required to create a company")

            obj.association = self.request.user.associationprofile

        if commit:
            obj.save()
            self.save_m2m()

        return obj



class CaseStudyForm(forms.ModelForm):
    company = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        label="Company",
    )

    class Meta:
        model = CaseStudy
        fields = [
            "title",
            "company",
            "logo",
            "description",
            "revenue_split_notes",
            "time_estimate",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "revenue_split_notes": forms.Textarea(attrs={"rows": 3}),
            "logo": forms.FileInput(),
        }

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

        if not request or not hasattr(request.user, "associationprofile"):
            self.fields["company"].queryset = Company.objects.none()
            return

        association = request.user.associationprofile

        self.fields["company"].queryset = Company.objects.filter(
            association=association
        )

        self.fields["company"].label_from_instance = (
            lambda obj: f"{obj.name} — {obj.get_status_display()}"
        )

    def clean_company(self):
        company = self.cleaned_data["company"]

        if not hasattr(self.request.user, "associationprofile"):
            raise forms.ValidationError("Only associations can create case studies.")

        if company.association_id != self.request.user.associationprofile.id:
            raise forms.ValidationError(
                "You may only create case studies for your own companies."
            )

        return company


class ResearchGroupForm(forms.ModelForm):
    class Meta:
        model = ResearchGroup
        fields = ['name', 'lead_professor', 'description', 'contact_email']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_contact_email(self):
        return validate_email(self.cleaned_data['contact_email'])

class ApplicationForm(forms.ModelForm):

    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        empty_label="Select a Project (optional)",
    )

    case_study = forms.ModelChoiceField(
        queryset=CaseStudy.objects.all(),
        required=False,
        empty_label="Select a Case Study (optional)",
    )

    class Meta:
        model = Application
        fields = [
            'project', 'case_study',
            'experience', 'motivation',
            'interest', 'comments'
        ]
        widgets = {
            'experience': forms.Textarea(attrs={'rows': 4}),
            'motivation': forms.Textarea(attrs={'rows': 4}),
            'interest': forms.Textarea(attrs={'rows': 4}),
            'comments': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': (
                    "Optional: If you are applying for your own project idea, "
                    "describe it here. If you have any other comments, add them here."
                )
            }),
        }

    def __init__(self, *args, request=None, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)

        if request is None:
            return

        # Hide case study if project pre-filled
        if instance and instance.project:
            self.fields.pop("case_study", None)

        # Hide project if case study pre-filled
        elif instance and instance.case_study:
            self.fields.pop("project", None)

        # Custom labels for dropdowns
        if "project" in self.fields:
            self.fields['project'].label_from_instance = (
                lambda obj: f"{obj.title} (Supervisor: {obj.supervisor.user.display_name})"
            )

        if "case_study" in self.fields:
            self.fields['case_study'].label_from_instance = (
                lambda obj: f"{obj.title} ({obj.company.name})"
            )

        # Instructions displayed in the template
        self.instructions = (
            "Please fill in the details below. Only one of Project or Case Study may be selected. "
            "We will process your application and contact you via your account email. "
            "There is no fixed processing time."
        )

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project")
        case_study = cleaned_data.get("case_study")

        # Only one or neither may be selected
        if project and case_study:
            raise forms.ValidationError(
                "You may select either a project OR a case study, not both."
            )

        return cleaned_data

# forms.py
class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status"]



