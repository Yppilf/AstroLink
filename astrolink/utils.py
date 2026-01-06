from .models import Application
from django.db.models import Q

def get_applications_for_user(user):
    role = user.role.name if user.role else None

    qs = Application.objects.select_related(
        "member",
        "project",
        "project__supervisor",
        "project__supervisor__user",
        "case_study",
        "case_study__company",
        "case_study__company__association",
    )

    # STUDENT: applications they submitted
    if role == "Student":
        return qs.filter(member=user)

    # SUPERVISOR: applications to their projects
    if role == "Supervisor":
        return qs.filter(
            project__supervisor__user=user
        )

    # ASSOCIATION: applications to their companies' case studies
    # + general applications (no project, no case study)
    if role == "Association":
        return qs.filter(
            Q(
                case_study__company__association__user=user
            ) |
            Q(
                project__isnull=True,
                case_study__isnull=True
            )
        )

    return Application.objects.none()