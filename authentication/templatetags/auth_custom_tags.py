from django import template

register = template.Library()

@register.filter
def pretty_header(value):
    """Converts snake_case or field names to 'Pretty Header'"""
    return value.replace("_", " ").title()
