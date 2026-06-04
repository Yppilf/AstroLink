from django.db import models
from authentication.models import User

class RawEvent(models.Model):
    timestamp = models.DateTimeField(db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    section = models.CharField(max_length=50, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["timestamp", "section"]),
        ]

class HourlyAggregate(models.Model):
    period_start = models.DateTimeField(db_index=True)
    section = models.CharField(max_length=50)
    total_requests = models.IntegerField()
    unique_visitors = models.IntegerField()
    unique_visitors_hll = models.BinaryField()

    class Meta:
        unique_together = ("period_start", "section")

class AggregationState(models.Model):
    last_aggregated_hour = models.DateTimeField()
