from .models import Application
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from authentication.models import CoordinatorProfile, StudentProfile
from permissions.utils import has_permission
from itertools import chain

def get_full_url(path):
    """
    Converts a relative path to a full absolute URL using SITE_URL.
    Fallback: use request.get_host() if needed.
    """
    site_url = getattr(settings, "SITE_URL", "https://siriusa.nl")  # your main domain
    return f"{site_url.rstrip('/')}{path}"

def get_applications_for_user(request_user, target_user):
    role = request_user.role.name if request_user.role else None
    target_role = target_user.role.name if target_user.role else None

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
    # SELF VIEW: STUDENT
    # -------------------------
    if request_user == target_user and role == "Student":
        return qs.filter(member=target_user)

    # -------------------------
    # SELF VIEW: SUPERVISOR
    # -------------------------
    if request_user == target_user and role == "Supervisor":
        return qs.filter(
            project__supervisor__user=target_user
        )

    # -------------------------
    # SELF VIEW: ASSOCIATION
    # -------------------------
    if request_user == target_user and role == "Association":
        return qs.filter(
            Q(case_study__company__association__user=target_user)
            | Q(association__user=target_user)
        )

    # -------------------------
    # PROGRAMME COORDINATOR VIEW
    # -------------------------
    if has_permission(request_user, "read_student") and request_user != target_user:

        coordinator_student_user_ids = (
            get_students_for_coordinator(request_user)
            .values_list("user_id", flat=True)
        )

        # Coordinator viewing a student profile
        if target_role == "Student":
            return (
                qs.filter(
                    member=target_user
                )
                .filter(thesis_application_q())
                .distinct()
                .order_by("-updated_at")
            )

        # Coordinator viewing a supervisor profile
        if target_role == "Supervisor":
            return (
                qs.filter(
                    project__supervisor__user=target_user,
                    member_id__in=coordinator_student_user_ids,
                )
                .filter(thesis_application_q())
                .distinct()
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

def build_application_timeline(applications):
    events = []

    for app in applications:
        base = {
            "application_id": app.id,
            "student": app.member.display_name(),
            "project": app.project.title if app.project else None,
            "case_study": app.case_study.title if app.case_study else None,
        }

        # CREATED
        events.append({
            "type": "APPLICATION_CREATED",
            "timestamp": app.created_at,
            **base,
        })

        # ACCEPTED
        if app.accepted_at:
            events.append({
                "type": "APPLICATION_ACCEPTED",
                "timestamp": app.accepted_at,
                **base,
            })

        # REJECTED
        if app.rejected_at:
            events.append({
                "type": "APPLICATION_REJECTED",
                "timestamp": app.rejected_at,
                **base,
            })

        # CONFIRMED
        if app.confirmed_at:
            events.append({
                "type": "APPLICATION_CONFIRMED",
                "timestamp": app.confirmed_at,
                **base,
            })

        # DOCUMENTS
        for doc in app.documents.all():
            doc_base = {
                **base,
                "document_id": doc.id,
                "document_name": doc.name,
            }

            events.append({
                "type": "DOCUMENT_CREATED",
                "timestamp": doc.created_at,
                **doc_base,
            })

            if doc.last_edited_at:
                events.append({
                    "type": "DOCUMENT_EDITED",
                    "timestamp": doc.last_edited_at,
                    **doc_base,
                })

            if doc.locked_at:
                events.append({
                    "type": "DOCUMENT_LOCKED",
                    "timestamp": doc.locked_at,
                    **doc_base,
                })

    return sorted(events, key=lambda x: x["timestamp"], reverse=True)

def get_coordinator_timeline_queryset(
    *,
    coordinator_user,
    student=None,
    supervisor=None,
    project=None,
    case_study=None,
):
    """
    Coordinator-only timeline access.
    All filters are strictly scoped to coordinator permissions.
    """

    coordinator_students = get_students_for_coordinator(coordinator_user)
    coordinator_student_user_ids = coordinator_students.values_list("user_id", flat=True)

    qs = (
        Application.objects
        .select_related(
            "member",
            "project",
            "project__supervisor",
            "case_study",
            "case_study__company",
        )
        .prefetch_related("documents")
        .filter(thesis_application_q())
    )

    # -------------------------
    # STUDENT FILTER (restricted)
    # -------------------------
    if student:
        if student.id not in coordinator_student_user_ids:
            return Application.objects.none()

        qs = qs.filter(member=student)

    else:
        qs = qs.filter(member_id__in=coordinator_student_user_ids)

    # -------------------------
    # SUPERVISOR FILTER (restricted to thesis projects only)
    # -------------------------
    if supervisor:
        qs = qs.filter(project__supervisor__user=supervisor)

    # -------------------------
    # PROJECT FILTER (must be thesis)
    # -------------------------
    if project:
        qs = qs.filter(project=project)

    # -------------------------
    # CASE STUDY FILTER (must be thesis)
    # -------------------------
    if case_study:
        qs = qs.filter(case_study=case_study)

    return qs

from django.db.models import F, Value
from django.db.models.functions import Coalesce, Concat
def get_coordinator_timeline_options(user):
    from astrolink.models import Project, CaseStudy
    from authentication.models import User

    # -------------------------
    # STUDENTS (coordinator scoped)
    # -------------------------
    students = (
        get_students_for_coordinator(user)
        .select_related("user")
        .annotate(
            display_name=Coalesce(
                "user__screen_name",
                "user__legal_name",
                Concat("user__first_name", Value(" "), "user__last_name"),
            )
        )
    )

    # -------------------------
    # SUPERVISORS
    # -------------------------
    supervisors = (
        User.objects
        .filter(supervisorprofile__isnull=False)
        .annotate(
            display_name=Coalesce(
                "screen_name",
                "legal_name",
                Concat("first_name", Value(" "), "last_name"),
            )
        )
        .distinct()
    )

    # -------------------------
    # PROJECTS (thesis only)
    # -------------------------
    projects = (
        Project.objects
        .filter(tags__slug="thesis")
        .annotate(display_name=F("title"))
        .distinct()
    )

    # -------------------------
    # CASE STUDIES (thesis only)
    # -------------------------
    case_studies = (
        CaseStudy.objects
        .filter(tags__slug="thesis")
        .annotate(display_name=F("title"))
        .distinct()
    )

    return students, supervisors, projects, case_studies