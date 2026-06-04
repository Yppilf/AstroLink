from django.utils.timezone import now
from django.db.utils import OperationalError, ProgrammingError
from .models import RawEvent
from .aggregation import should_attempt_aggregation, aggregate_completed_hours


IGNORED_PATH_PREFIXES = (
    "/static/",
    "/media/",
    "/favicon.ico",
)


def resolve_section(request):
    """
    Use first URL path segment:
    /documents/16/edit -> documents
    /profile/edit -> profile
    """
    path = request.path.strip("/")

    if not path:
        return "root"

    return path.split("/")[0][:50]


class AuthenticatedAnalyticsMiddleware:
    """
    Only tracks authenticated users.
    No anonymous visitor tracking.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        try:
            # 1. only authenticated users
            if not request.user.is_authenticated:
                return response

            # 2. only GET
            if request.method != "GET":
                return response

            # 3. ignore static/media
            if request.path.startswith(IGNORED_PATH_PREFIXES):
                return response

            # 4. only successful HTML pages
            if response.status_code != 200:
                return response

            if "text/html" not in response.get("Content-Type", ""):
                return response

            # 5. ignore AJAX
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return response

            section = resolve_section(request)

            RawEvent.objects.create(
                timestamp=now(),
                user=request.user,
                section=section,
            )

            if should_attempt_aggregation():
                aggregate_completed_hours()

        except (OperationalError, ProgrammingError):
            pass

        return response