from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def navactive(context, *url_names):
    """
    Returns 'active' if the current URL name matches any of the provided ones.
    """
    current = context['request'].resolver_match.url_name
    return "active" if current in url_names else ""
