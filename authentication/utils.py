from .models import User, StudentProfile, SupervisorProfile, AssociationProfile
from .forms import StudentProfileForm, SupervisorProfileForm, AssociationProfileForm

PROFILE_REGISTRY = {
    "Student": {
        "model": StudentProfile,
        "form": StudentProfileForm,
        "label": "Student",
    },
    "Supervisor": {
        "model": SupervisorProfile,
        "form": SupervisorProfileForm,
        "label": "Supervisor",
        "extra_context_fn": lambda profile: {
            "references": profile.references.all(),
            "projects": profile.projects.all(),
        }
    },
    "Association": {
        "model": AssociationProfile,
        "form": AssociationProfileForm,
        "label": "Association",
    },
}

def assign_role(user, role):
    user.role = role
    user.save(update_fields=["role"])

    registry_entry = PROFILE_REGISTRY.get(role.name)
    if not registry_entry:
        return

    profile_model = registry_entry["model"]
    profile_model.objects.get_or_create(user=user)


def model_to_field_pairs(instance, exclude=None):
    exclude = exclude or []
    data = []
    for field in instance._meta.fields:
        if field.name in exclude:
            continue
        value = getattr(instance, field.name)
        if value not in ("", None):
            data.append((field.verbose_name.title(), value))
    return data
