# Metrics Collection App

## Purpose

The `metrics` app provides lightweight, authenticated usage analytics for AstroLink. It is designed to track how authenticated users interact with the platform, aggregate that activity efficiently, and expose it through a dashboard for administrators or programme coordinators.

Unlike external analytics tools, this system is fully self-contained, privacy-preserving, and tightly integrated with Django authentication and permissions.

Only authenticated user activity is tracked. Anonymous traffic is explicitly ignored.

---

# High-Level Architecture

The metrics system is composed of three layers:

1. Event ingestion (middleware)
2. Background aggregation (hourly rollups)
3. Dashboard visualization (charts + tables)

```text
Authenticated Request
        ↓
Middleware (AuthenticatedAnalyticsMiddleware)
        ↓
RawEvent (high-volume event log)
        ↓
Aggregation worker (aggregate_completed_hours)
        ↓
HourlyAggregate (compressed analytics storage)
        ↓
Dashboard (Chart.js + tables)
```

---

# Data Model

## RawEvent (High-Volume Event Log)

Stores individual user interactions before aggregation.

```python
class RawEvent(models.Model):
    timestamp = models.DateTimeField(db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    section = models.CharField(max_length=50, db_index=True)
```

### Purpose

* Captures each tracked page request
* Minimal schema for high write throughput
* Designed for short retention (events are deleted after aggregation)

### Indexed Fields

* `timestamp`
* `(timestamp, section)`

---

## HourlyAggregate (Aggregated Metrics)

Stores precomputed metrics per hour and section.

```python
class HourlyAggregate(models.Model):
    period_start = models.DateTimeField(db_index=True)
    section = models.CharField(max_length=50)
    total_requests = models.IntegerField()
    unique_visitors = models.IntegerField()
```

### Purpose

* Enables fast querying for dashboards
* Replaces raw events after aggregation
* Supports multi-dimensional grouping (time + section)

### Constraints

* Unique per `(period_start, section)`

---

## AggregationState (Progress Tracking)

Tracks how far the system has processed raw events.

```python
class AggregationState(models.Model):
    last_aggregated_hour = models.DateTimeField()
```

### Purpose

* Ensures incremental aggregation
* Prevents duplicate processing
* Allows safe restart after downtime

---

# Event Collection (Middleware)

## AuthenticatedAnalyticsMiddleware

This middleware is responsible for collecting analytics data at request time.

### Key Design Principle

Only successful, authenticated, human page views are tracked.

---

## Filtering Rules

The middleware excludes:

* Anonymous users
* Non-GET requests
* Static/media assets
* Failed responses (non-200)
* Non-HTML responses
* AJAX requests

```python
if not request.user.is_authenticated:
    return response

if request.method != "GET":
    return response

if request.path.startswith(IGNORED_PATH_PREFIXES):
    return response
```

---

## Section Resolution

Each event is categorized by the first URL segment:

```python
def resolve_section(request):
    path = request.path.strip("/")
    return path.split("/")[0][:50] if path else "root"
```

### Examples

| URL                | Section      |
| ------------------ | ------------ |
| `/projects/12/`    | projects     |
| `/applications/5/` | applications |
| `/profile/edit`    | profile      |
| `/`                | root         |

---

## Event Recording

After filtering:

```python
RawEvent.objects.create(
    timestamp=now(),
    user=request.user,
    section=section,
)
```

---

## Triggering Aggregation

After each event, the system opportunistically attempts aggregation:

```python
if should_attempt_aggregation():
    aggregate_completed_hours()
```

This ensures aggregation runs incrementally without a scheduled job system.

---

# Aggregation System

## Overview

The aggregation layer compresses raw events into hourly summaries and deletes processed data.

This ensures:

* Stable database size
* Fast dashboard queries
* Predictable performance at scale

---

## Locking Strategy

To avoid concurrent aggregation:

```python
def should_attempt_aggregation():
    return cache.add("metrics:aggregate_lock", True, timeout=60)
```

This ensures only one worker runs aggregation per minute.

---

## Aggregation Logic

### Step 1: Load State

```python
state, _ = AggregationState.objects.select_for_update().get_or_create(
    id=1,
    defaults={"last_aggregated_hour": floor_to_hour(now()) - timedelta(hours=1)}
)
```

---

### Step 2: Determine Target Range

The system processes one hour at a time:

```python
target_hour = state.last_aggregated_hour + timedelta(hours=1)
```

---

### Step 3: Process Events

For each hour:

* Fetch events in range
* Group by section
* Compute:

  * total requests
  * unique users

```python
aggregates[section]["users"].add(event.user_id)
```

---

### Step 4: Store Aggregates

```python
HourlyAggregate.objects.update_or_create(
    period_start=target_hour,
    section=section,
    defaults={
        "total_requests": ...,
        "unique_visitors": ...,
    }
)
```

---

### Step 5: Cleanup

After processing:

* Delete raw events
* Advance aggregation state

```python
events.delete()
state.last_aggregated_hour = target_hour
state.save()
```

---

## Design Trade-offs

### Pros

* Constant storage growth (bounded)
* Efficient dashboards
* Simple architecture (no external queue system)

### Cons

* Aggregation runs in request cycle (lightweight but not background isolated)
* Slight write overhead per request
* Not suitable for extremely high traffic systems without offloading

---

# Metrics Dashboard

## Overview

The dashboard visualizes aggregated metrics using:

* Hourly trends
* Daily trends
* Weekly trends
* Per-section breakdowns
* Unique visitors and total requests

---

## Query Strategy

All queries operate on `HourlyAggregate` only.

### Time Window

```python
since = now() - timedelta(days=30)
```

---

## Aggregation Levels

### Hourly

```python
.values("period_start", "section")
.annotate(total_requests=Sum(...))
```

### Daily

```python
.annotate(day=TruncDate("period_start"))
```

### Weekly

```python
.annotate(week=TruncWeek("period_start"))
```

---

## Data Serialization

Results are serialized to JSON for frontend visualization:

```python
json.dumps(list(hourly_stats), cls=DjangoJSONEncoder)
```

---

# Frontend Visualization

## Stack

* Chart.js (bar charts)
* Vanilla JavaScript
* Django templating system

---

## UI Structure

Each metric block includes:

* Paginated table
* Interactive bar chart
* Section-based grouping
* Time-based grouping (hour/day/week)

---

## Component System

Each chart is rendered using a reusable template:

```django
{% include "metrics/_metrics_stats_component.html" %}
```

This avoids duplication across:

* hourly requests
* hourly visitors
* daily requests
* daily visitors
* weekly requests
* weekly visitors

---

## Client-Side Processing

The frontend:

### 1. Groups data by time bucket

```js
groupByTime(rawData)
```

### 2. Builds pagination pages

```js
buildPages(grouped)
```

### 3. Formats timestamps

* Hourly → datetime format
* Daily → date format
* Weekly → week start label

---

## Chart Rendering

Each page renders a stacked bar chart:

* X-axis: time period
* Y-axis: request/visitor count
* Series: section names

```js
type: "bar"
```

---

## Pagination Behavior

* Fixed page size (12 grouped entries)
* Navigation controls:

  * Previous / Next
  * Jump-to dropdown

---

# Performance Characteristics

## Write Path

* O(1) insert per request
* Minimal middleware overhead

## Aggregation Path

* O(n) per hour batch
* Uses iterator for memory efficiency
* Deletes raw data after processing

## Read Path

* Fully indexed aggregate queries
* No raw event scanning in dashboard

---

# Scalability Considerations

This system is designed to scale to moderate-to-high traffic workloads due to:

### Strengths

* Event compression via hourly aggregation
* Raw event cleanup
* Indexed queries
* Cache-based aggregation lock
* No external dependencies

### Potential Bottlenecks

* Middleware writes on every request
* Aggregation runs inside request cycle
* Large spikes may delay aggregation

---

# Summary

The Metrics app provides a lightweight, privacy-focused analytics system that:

* Tracks authenticated user activity
* Aggregates data hourly to reduce storage overhead
* Provides fast dashboard visualization
* Avoids external analytics dependencies

It is intentionally simple, Django-native, and designed for maintainability over extreme scalability.
