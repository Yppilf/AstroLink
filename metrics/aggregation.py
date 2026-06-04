from django.db import transaction
from django.utils.timezone import now
from datetime import timedelta
from .models import RawEvent, HourlyAggregate, AggregationState
from .utils import floor_to_hour
from django.db.models import Sum, Count
from django.core.cache import cache
import hyperloglog, pickle

def should_attempt_aggregation():
    return cache.add("metrics:aggregate_lock", True, timeout=60)

@transaction.atomic
def aggregate_completed_hours():
    state, _ = AggregationState.objects.select_for_update().get_or_create(
        id=1,
        defaults={"last_aggregated_hour": floor_to_hour(now()) - timedelta(hours=1)}
    )

    current_hour = floor_to_hour(now())
    target_hour = state.last_aggregated_hour + timedelta(hours=1)

    while target_hour < current_hour:
        events = RawEvent.objects.filter(
            timestamp__gte=target_hour,
            timestamp__lt=target_hour + timedelta(hours=1),
        )

        aggregates = {}

        for event in events.only("visitor_id", "section").iterator(chunk_size=1000):
            key = event.section

            if key not in aggregates:
                aggregates[key] = {
                    "total_requests": 0,
                    "hll": hyperloglog.HyperLogLog(0.01),  # ~1% error
                }

            aggregates[key]["total_requests"] += 1
            aggregates[key]["hll"].add(event.visitor_id)

        for section, data in aggregates.items():
            hll = data["hll"]

            HourlyAggregate.objects.update_or_create(
                period_start=target_hour,
                section=section,
                defaults={
                    "total_requests": data["total_requests"],
                    "unique_visitors": len(hll),
                    "unique_visitors_hll": pickle.dumps(hll),
                }
            )

        events.delete()
        state.last_aggregated_hour = target_hour
        state.save(update_fields=["last_aggregated_hour"])

        target_hour += timedelta(hours=1)
