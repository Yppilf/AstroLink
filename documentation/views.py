from django.shortcuts import render, redirect
from pathlib import Path
from .docs_config import DOCS_NAV
from .templatetags.markdown_extras import render_markdown

BASE_DIR = Path(__file__).resolve().parent  # this is your app folder

def docs_page(request, slug):
    file_path = BASE_DIR / "docs" / f"{slug}.md"

    if not file_path.exists():
        return render(request, "forum/404.html")

    content = file_path.read_text(encoding="utf-8")

    rendered = render_markdown(content)

    return render(request, "documentation/page.html", {
        "html": rendered["html"],
        "toc": rendered["toc"],
        "docs_nav": DOCS_NAV,
        "current_slug": slug,
    })

def home(request):
    return redirect("documentation:docs_page", "home")