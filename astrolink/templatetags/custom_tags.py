from django import template

register = template.Library()

@register.filter
def get_display(obj, field_name):
    """Returns get_<field_name>_display() if it exists, otherwise normal attribute"""
    getter_name = f"get_{field_name}_display"
    if hasattr(obj, getter_name):
        return getattr(obj, getter_name)()
    return getattr(obj, field_name, "")

@register.filter
def pretty_header(value):
    """Convert snake_case to Title Case for table headers."""
    return str(value).replace("_", " ").title()