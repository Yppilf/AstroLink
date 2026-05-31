from .models import User, StudentProfile, SupervisorProfile, AssociationProfile, CoordinatorProfile
from .forms import StudentProfileForm, SupervisorProfileForm, AssociationProfileForm, CoordinatorProfileForm

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
    "Programme Coordinator": {
        "model": CoordinatorProfile,
        "form": CoordinatorProfileForm,
        "label": "Programme Coordinator",
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
    pairs = []

    for field in instance._meta.fields:
        if field.name in exclude:
            continue

        display_method = f"get_{field.name}_display"

        if hasattr(instance, display_method):
            value = getattr(instance, display_method)()
        else:
            value = getattr(instance, field.name)

        pairs.append((field.verbose_name.title(), value))

    return pairs