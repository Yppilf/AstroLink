from .models import Application
from django.db.models import Q

def get_applications_for_user(user):
    role = user.role.name if user.role else None

    qs = Application.objects.select_related(
        "member", "project", "project__supervisor", "project__supervisor__user",
        "case_study", "case_study__company"
    )

    # STUDENT: applications they submitted
    if role == "Student":
        return qs.filter(member=user)

    # SUPERVISOR: applications for their projects
    if role == "Supervisor":
        return qs.filter(
            project__supervisor__user=user
        )

    # ASSOCIATION (future): case studies or unassigned
    if role == "Association":
        return qs.filter(
            Q(case_study__isnull=False) |
            Q(project__isnull=True, case_study__isnull=True)
        )

    # Default: nothing
    return Application.objects.none()