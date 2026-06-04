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

    hourly_stats = (
        qs.values("period_start", "section")
        .annotate(
            total_requests=Sum("total_requests"),
            unique_visitors=Sum("unique_visitors"),
        )
        .order_by("-period_start")
    )

    # DAILY
    daily_data = {}

    for row in qs.annotate(day=TruncDate("period_start")):
        key = (row.day, row.section)

        if key not in daily_data:
            daily_data[key] = {
                "total_requests": 0,
                "hll": hyperloglog.HyperLogLog(0.01),
            }

        daily_data[key]["total_requests"] += row.total_requests
        daily_data[key]["hll"].update(pickle.loads(row.unique_visitors_hll))

    daily_stats = [
        {
            "day": day,
            "section": section,
            "total_requests": data["total_requests"],
            "unique_visitors": len(data["hll"]),
        }
        for (day, section), data in daily_data.items()
    ]

    daily_stats.sort(key=lambda x: x["day"], reverse=True)

    # WEEKLY
    weekly_data = {}

    for row in qs.annotate(week=TruncWeek("period_start")):
        key = (row.week, row.section)

        if key not in weekly_data:
            weekly_data[key] = {
                "total_requests": 0,
                "hll": hyperloglog.HyperLogLog(0.01),
            }

        weekly_data[key]["total_requests"] += row.total_requests
        weekly_data[key]["hll"].update(pickle.loads(row.unique_visitors_hll))

    weekly_stats = [
        {
            "week": week,
            "section": section,
            "total_requests": data["total_requests"],
            "unique_visitors": len(data["hll"]),
        }
        for (week, section), data in weekly_data.items()
    ]

    weekly_stats.sort(key=lambda x: x["week"], reverse=True)

    return render(request, "metrics/dashboard.html", {
        "hourly_stats_json": json.dumps(list(hourly_stats), cls=DjangoJSONEncoder),
        "daily_stats_json": json.dumps(daily_stats, cls=DjangoJSONEncoder),
        "weekly_stats_json": json.dumps(weekly_stats, cls=DjangoJSONEncoder),
    })