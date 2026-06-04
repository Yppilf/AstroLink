from django.utils.timezone import now

def floor_to_hour(dt):
    return dt.replace(minute=0, second=0, microsecond=0)