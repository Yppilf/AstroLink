import markdown
import bleach
from django import template

register = template.Library()

# --- Safe handling of allowed tags ---
# Bleach 5.x+ sometimes provides ALLOWED_TAGS as a list instead of a set.
_base_allowed_tags = getattr(bleach.sanitizer, "ALLOWED_TAGS", [])
# Always convert to a set for safe modification
ALLOWED_TAGS = set(_base_allowed_tags)

# Add your custom tags
ALLOWED_TAGS.update({
    'p', 'pre', 'code', 'span', 'div', 'br', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'strong', 'em', 'blockquote'
})

# --- Safe handling of allowed attributes ---
# Allow specific HTML attributes
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'style'],
    'span': ['class'],
    'code': ['class'],
}

@register.filter(name='render')
def render_markdown_safe(text):
    """
    Renders Markdown safely, allowing only whitelisted tags and attributes.
    """
    if not text:
        return ""

    html = markdown.markdown(
        text,
        extensions=["fenced_code", "codehilite", "nl2br", "tables"]
    )

    sanitized = bleach.clean(
        html,
        tags=list(ALLOWED_TAGS),
        attributes=ALLOWED_ATTRIBUTES,
        strip=True                         # Strip disallowed tags instead of escaping
    )

    return sanitized
