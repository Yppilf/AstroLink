import json
import pickle
import hyperloglog

from django.shortcuts import render
from django.utils.timezone import now, timedelta
from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncWeek
from django.core.serializers.json import DjangoJSONEncoder

from .models import HourlyAggregate
from permissions.utils import external_user_permissions_required


@external_user_permissions_required("read_metrics")
def metrics_dashboard(request):

    since = now() - timedelta(days=30)

    qs = HourlyAggregate.objects.filter(period_start__gte=since)

    # -------------------
    # HOURLY
    # -------------------
    hourly_stats = (
        qs.values("period_start", "section")
        .annotate(
            total_requests=Sum("total_requests"),
            unique_visitors=Sum("unique_visitors"),
        )
        .order_by("-period_start")
    )

    # -------------------
    # DAILY
    # -------------------
    daily_stats = (
        qs.annotate(day=TruncDate("period_start"))
        .values("day", "section")
        .annotate(
            total_requests=Sum("total_requests"),
            unique_visitors=Sum("unique_visitors"),
        )
        .order_by("-day")
    )

    # -------------------
    # WEEKLY
    # -------------------
    weekly_stats = (
        qs.annotate(week=TruncWeek("period_start"))
        .values("week", "section")
        .annotate(
            total_requests=Sum("total_requests"),
            unique_visitors=Sum("unique_visitors"),
        )
        .order_by("-week")
    )

    return render(request, "metrics/dashboard.html", {
        "hourly_stats_json": json.dumps(list(hourly_stats), cls=DjangoJSONEncoder),
        "daily_stats_json": json.dumps(list(daily_stats), cls=DjangoJSONEncoder),
        "weekly_stats_json": json.dumps(list(weekly_stats), cls=DjangoJSONEncoder),

        "hourly_headers": ["Hour", "Section", "Requests"],
        "daily_headers": ["Date", "Section", "Requests"],
        "weekly_headers": ["Week", "Section", "Requests"],
    })