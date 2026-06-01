from django.db.models import Q
from django.http import JsonResponse

from authentication.models import SupervisorProfile


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