import markdown, re
from django import template
import html as html_lib  # for escaping

register = template.Library()

@register.filter
def render_markdown(value):
    # Handle custom components before rendering
    # Inline version
    value = re.sub(
        r"\[breadcrumb-inline:(.*?)\]",
        lambda m: render_breadcrumb(m.group(1), inline=True),
        value
    )

    # Block version
    value = re.sub(
        r"\[breadcrumb:(.*?)\]",
        lambda m: render_breadcrumb(m.group(1), inline=False),
        value
    )

    md = markdown.Markdown(extensions=["toc", "fenced_code", "tables"])
    html = md.convert(value)
    toc = md.toc

    # Custom button syntax: [button:Text]
    html = re.sub(
        r"\[button:(.*?)(\|link=(.*?))?\]",
        lambda m: f'<a href="{m.group(3) or "#"}" class="btn btn-primary">{m.group(1)}</a>',
        html
    )

    html = re.sub(
        r"\[alert:(.*?)\]",
        r'<div class="alert alert-warning">\1</div>',
        html
    )

    html = re.sub(
        r'<img src="(.*?)" alt="(.*?)">',
        r'''
        <div class="doc-image my-4 text-center">
            <img src="\1" alt="\2" class="img-fluid rounded shadow">
            <small class="text-muted d-block">\2</small>
        </div>
        ''',
        html
    )

    return {"html": html, "toc": toc}

def render_breadcrumb(text, inline=False):
    parts = [p.strip() for p in text.split("::")]

    items = []

    for i, part in enumerate(parts):
        if "|" in part:
            label, link = part.split("|", 1)
        else:
            label, link = part, None

        label = html_lib.escape(label.strip())

        if link and i != len(parts) - 1:
            items.append(f'<a href="{link}" class="doc-crumb-link">{label}</a>')
        else:
            items.append(f'<span class="doc-crumb-active">{label}</span>')

    if inline:
        return f'<span class="doc-breadcrumb-inline">{" &rsaquo; ".join(items)}</span>'
    else:
        items_html = "".join([
            f'<li class="breadcrumb-item">{item}</li>'
            if "a href" in item else
            f'<li class="breadcrumb-item active">{item}</li>'
            for item in items
        ])

        return f'''
        <div class="doc-breadcrumb">
            <nav aria-label="breadcrumb" class="my-3">
                <ol class="breadcrumb">
                    {items_html}
                </ol>
            </nav>
        </div>
        '''