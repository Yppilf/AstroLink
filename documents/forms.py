from django import forms
from .models import TemplateField, TemplateAsset, DocumentTemplate
from authentication.models import User
from authentication.widgets import StudentUserSearchWidget, SupervisorUserSearchWidget, CoordinatorUserSearchWidget, AssociationUserSearchWidget

class DocumentTemplateForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplate
        fields = ["name", "description", "latex_file", "name_template"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

class TemplateAssetForm(forms.ModelForm):
    class Meta:
        model = TemplateAsset
        fields = ["file", "name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }

class TemplateFieldForm(forms.ModelForm):
    choices_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Enter one choice per line (e.g. yes\nno)"
        }),
        help_text="Only used for 'choice' field type"
    )

    class Meta:
        model = TemplateField
        fields = [
            "name",
            "label",
            "field_type",
            "choices_text",
            "default_value",
            "required",
            "allowed_roles",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "field_type": forms.Select(attrs={"class": "form-select"}),
            "default_value": forms.TextInput(attrs={"class": "form-control"}),
            "allowed_roles": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.choices:
            self.fields["choices_text"].initial = "\n".join(self.instance.choices)

    def clean_choices_text(self):
        data = self.cleaned_data.get("choices_text")

        if not data:
            return None

        # split by lines
        choices = [line.strip() for line in data.splitlines() if line.strip()]

        return choices
    
    def clean(self):
        cleaned = super().clean()

        field_type = cleaned.get("field_type")
        choices = cleaned.get("choices_text")

        if field_type == "choice" and not choices:
            self.add_error("choices_text", "Choices are required for choice fields.")

        if field_type != "choice":
            cleaned["choices_text"] = None

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.choices = self.cleaned_data.get("choices_text")

        if commit:
            instance.save()
            self.save_m2m()

        return instance
    
def build_dynamic_form(template, preview=False):
    class DynamicForm(forms.Form):
        pass

    for f in template.fields.all():
        required = False if preview else f.required

        if f.field_type == "integer":
            field = forms.IntegerField(required=required, label=f.label, widget=forms.TextInput(attrs={"class": "form-control"}))

        elif f.field_type == "float":
            field = forms.FloatField(required=required, label=f.label, widget=forms.TextInput(attrs={"class": "form-control"}))

        elif f.field_type == "date":
            field = forms.DateField(
                required=required,
                label=f.label,
                widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
            )

        elif f.field_type == "boolean":
            field = forms.BooleanField(required=False, label=f.label, widget=forms.TextInput(attrs={"class": "form-control"}))

        elif f.field_type == "choice":
            field = forms.ChoiceField(
                required=required,
                label=f.label,
                choices=[(c, c) for c in (f.choices or [])],
                widget=forms.Select(attrs={"class": "form-control"})
            )

        elif f.field_type == "signature":

            queryset = User.objects.filter(
                is_active=True,
                role__in=f.allowed_roles.all()
            )

            USER_SEARCH_WIDGETS = {
                "Student": StudentUserSearchWidget,
                "Supervisor": SupervisorUserSearchWidget,
                "Association": AssociationUserSearchWidget,
                "Programme Coordinator": CoordinatorUserSearchWidget,
            }

            role = f.allowed_roles.first()

            widget_class = USER_SEARCH_WIDGETS.get(
                role.name if role else None,
                StudentUserSearchWidget
            )

            widget = widget_class()

            field = forms.ModelChoiceField(
                queryset=queryset.distinct(),
                required=required,
                label=f.label,
                widget=widget
            )

        else:
            field = forms.CharField(
                required=required,
                label=f.label,
                widget=forms.TextInput(attrs={"class": "form-control"})
            )

        DynamicForm.base_fields[f.name] = field

    return DynamicForm