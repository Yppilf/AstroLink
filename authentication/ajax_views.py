from django.db.models import Q
from django.http import JsonResponse

from authentication.models import SupervisorProfile, User
from documents.models import TemplateField
from django.contrib.auth.decorators import login_required

@login_required
def supervisor_search(request):
    q = request.GET.get("q", "").strip()

    results = []

    if len(q) >= 2:

        supervisors = (
            SupervisorProfile.objects
            .select_related("user")
            .filter(
                academic_supervisor__isnull=True
            )
            .filter(
                Q(user__screen_name__icontains=q)
                |
                Q(user__legal_name__icontains=q)
            )
            [:20]
        )

        results = [
            {
                "id": supervisor.pk,
                "name": supervisor.user.display_name(),
            }
            for supervisor in supervisors
        ]

    return JsonResponse(results, safe=False)

@login_required
def student_user_search(request):
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    qs = User.objects.filter(
        is_active=True,
        role__name="Student"
    ).filter(
        Q(screen_name__icontains=q) |
        Q(legal_name__icontains=q)
    )[:20]

    return JsonResponse([
        {"id": u.pk, "name": u.display_name()}
        for u in qs
    ], safe=False)

@login_required
def supervisor_user_search(request):
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    qs = User.objects.filter(
        is_active=True,
        role__name="Supervisor"
    ).filter(
        Q(screen_name__icontains=q) |
        Q(legal_name__icontains=q)
    )[:20]

    return JsonResponse([
        {"id": u.pk, "name": u.display_name()}
        for u in qs
    ], safe=False)

@login_required
def association_user_search(request):
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    qs = User.objects.filter(
        is_active=True,
        role__name="Association"
    ).filter(
        Q(screen_name__icontains=q) |
        Q(legal_name__icontains=q)
    )[:20]

    return JsonResponse([
        {"id": u.pk, "name": u.display_name()}
        for u in qs
    ], safe=False)

@login_required
def coordinator_user_search(request):
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    qs = User.objects.filter(
        is_active=True,
        role__name="Programme Coordinator"
    ).filter(
        Q(screen_name__icontains=q) |
        Q(legal_name__icontains=q)
    )[:20]

    return JsonResponse([
        {"id": u.pk, "name": u.display_name()}
        for u in qs
    ], safe=False)