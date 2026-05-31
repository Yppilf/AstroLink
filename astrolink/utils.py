from .models import Application
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from authentication.models import CoordinatorProfile, StudentProfile
from permissions.utils import has_permission

def get_full_url(path):
    """
    Converts a relative path to a full absolute URL using SITE_URL.
    Fallback: use request.get_host() if needed.
    """
    site_url = getattr(settings, "SITE_URL", "https://siriusa.nl")  # your main domain
    return f"{site_url.rstrip('/')}{path}"

def get_applications_for_user(request_user, target_user):
    role = request_user.role.name if request_user.role else None

    qs = Application.objects.select_related(
        "member",
        "project",
        "project__supervisor",
        "project__supervisor__user",
        "case_study",
        "case_study__company",
        "case_study__company__association",
    )

    # -------------------------
    # STUDENT VIEW (self only)
    # -------------------------
    if request_user == target_user and role == "Student":
        return qs.filter(member=target_user)

    # -------------------------
    # SUPERVISOR VIEW
    # -------------------------
    if role == "Supervisor":
        return qs.filter(project__supervisor__user=request_user)

    # -------------------------
    # ASSOCIATION VIEW
    # -------------------------
    if role == "Association":
        return qs.filter(
            Q(case_study__company__association__user=request_user)
            | Q(association__user=request_user)
        )

    # -------------------------
    # PROGRAMME COORDINATOR VIEW
    # -------------------------
    if has_permission(request_user, "read_student") and request_user != target_user:
        return (
            qs.filter(member=target_user)
            .filter(thesis_application_q())
            .order_by("-updated_at")
        )

    return Application.objects.none()

def get_students_for_coordinator(user):
    coordinator = CoordinatorProfile.objects.filter(user=user).first()

    if not coordinator:
        return StudentProfile.objects.none()

    qs = StudentProfile.objects.select_related("user")

    if coordinator.study_programme:
        qs = qs.filter(study_programme=coordinator.study_programme)

    if coordinator.level:
        qs = qs.filter(level=coordinator.level)

    return qs

THESIS_APPLICATION_FILTER = (
    Q(user__member__project__tags__slug="thesis")
    |
    Q(user__member__case_study__tags__slug="thesis")
)

def thesis_application_q():
    return Q(project__tags__slug="thesis") | Q(case_study__tags__slug="thesis")