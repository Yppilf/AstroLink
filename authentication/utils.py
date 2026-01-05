from .models import User, StudentProfile, SupervisorProfile
from .forms import StudentProfileForm, SupervisorProfileForm

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


