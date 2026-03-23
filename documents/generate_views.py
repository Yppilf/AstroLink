import os
import time
import subprocess

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST

from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from django.utils import timezone
from django.core.files import File

from .models import DocumentTemplate, GeneratedDocument, DocumentSigner
from .forms import build_dynamic_form

from permissions.utils import external_user_permissions_required, has_permission, owns_generated_document

def generate_pdf(template, context_data, output_folder="generated", use_temp=True):
    base_dir = os.path.join(settings.MEDIA_ROOT, "generated_documents")

    if use_temp:
        base_dir = os.path.join(base_dir, "temp")

    output_dir = os.path.join(base_dir, output_folder)
    os.makedirs(output_dir, exist_ok=True)

    timestamp = int(time.time())
    safe_name = template.name.replace(" ", "_")

    filename_base = f"{safe_name}_{timestamp}"
    tex_file_path = os.path.join(output_dir, f"{filename_base}.tex")
    pdf_file_path = os.path.join(output_dir, f"{filename_base}.pdf")

    # ---------------------------
    # Load LaTeX template
    # ---------------------------
    template.latex_file.open()
    template_content = template.latex_file.read().decode("utf-8")
    template.latex_file.close()

    # ---------------------------
    # Jinja setup
    # ---------------------------
    env = Environment(
        loader=FileSystemLoader("/"),
        variable_start_string="<<",
        variable_end_string=">>",
        block_start_string="<%",
        block_end_string="%>",
        comment_start_string="<#",
        comment_end_string="#>"
    )

    env.filters.update({
        "money": lambda v: f"{float(v):.2f}" if v not in (None, "") else "0.00",
        "datefmt": lambda v: (
            datetime.strptime(v, "%Y-%m-%d").strftime("%d-%m-%Y")
            if isinstance(v, str) and len(v) == 10 else v
        ),
    })

    rendered_tex = env.from_string(template_content).render(**context_data)

    with open(tex_file_path, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    # ---------------------------
    # LaTeX compilation
    # ---------------------------
    env_vars = os.environ.copy()

    # IMPORTANT: include template-specific assets
    asset_paths = []
    for asset in template.assets.all():
        asset_paths.append(os.path.dirname(asset.file.path))

    env_vars["TEXINPUTS"] = os.pathsep.join(asset_paths) + os.pathsep + env_vars.get("TEXINPUTS", "")

    result = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_file_path],
        capture_output=True,
        text=True,
        env=env_vars
    )

    # Write log for debugging
    log_file = os.path.join(output_dir, f"{filename_base}.log")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(result.stdout)
        f.write(result.stderr)

    if not os.path.exists(pdf_file_path):
        raise RuntimeError(f"LaTeX failed. Check log: {log_file}")

    return pdf_file_path

def cleanup_temp_previews(folder="temp", max_age=300):
    base_dir = os.path.join(settings.MEDIA_ROOT, "generated_documents", folder)

    if not os.path.exists(base_dir):
        return

    now = time.time()

    for fname in os.listdir(base_dir):
        path = os.path.join(base_dir, fname)

        if not os.path.isfile(path):
            continue

        try:
            timestamp = int(fname.split("_")[-1].split(".")[0])
        except:
            continue

        if now - timestamp > max_age:
            os.remove(path)

@external_user_permissions_required('create_generateddocument', 'create_documentsigner')
def generate_document(request, template_id):
    template = get_object_or_404(DocumentTemplate, pk=template_id)
    DynamicForm = build_dynamic_form(template)

    form = DynamicForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        raw_context_data = form.cleaned_data.copy()
        context_data = {}

        # Convert signature fields to user IDs for JSON serialization
        for f in template.fields.all():
            value = raw_context_data.get(f.name)
            if f.field_type == "signature" and value:
                # store user id instead of User object
                context_data[f.name] = value.id
            else:
                context_data[f.name] = value

        # Generate PDF using the context_data
        pdf_path = generate_pdf(template, context_data, use_temp=False)

        # Create GeneratedDocument
        generated_doc = GeneratedDocument.objects.create(
            template=template,
            context_data=context_data,
            created_by=request.user if request.user.is_authenticated else None,
        )

        # Save PDF file
        filename = os.path.basename(pdf_path)
        with open(pdf_path, "rb") as f:
            generated_doc.pdf_file.save(filename, File(f), save=True)

        # Create DocumentSigner entries
        for f in template.fields.filter(field_type="signature"):
            user_id = context_data.get(f.name)
            if user_id:
                DocumentSigner.objects.create(
                    document=generated_doc,
                    field=f,
                    user_id=user_id
                )

        return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")

    return render(request, "documents/generate.html", {
        "template": template,
        "form": form,
    })

@require_POST
@external_user_permissions_required('create_generateddocument')
def generate_preview(request, template_id):
    template = get_object_or_404(DocumentTemplate, pk=template_id)
    DynamicForm = build_dynamic_form(template)

    form = DynamicForm(request.POST)

    if form.is_valid():
        context_data = form.cleaned_data

        pdf_path = generate_pdf(
            template,
            context_data,
            output_folder="previews",
            use_temp=True
        )

        # Convert file path → URL
        relative_path = os.path.relpath(
            pdf_path,
            settings.MEDIA_ROOT
        )

        pdf_url = settings.MEDIA_URL + relative_path.replace("\\", "/")

        # Cleanup old previews
        cleanup_temp_previews(folder="temp")

        return JsonResponse({"pdf_url": pdf_url})

    return JsonResponse({
        "error": form.errors
    }, status=400)

@external_user_permissions_required(
    "read_generateddocument",
    object_model=GeneratedDocument,
    ownership_checker=owns_generated_document
)
def generated_document_view(request, pk):
    """
    Serve the PDF file for a generated document in a new tab.
    """
    doc = get_object_or_404(GeneratedDocument, id=pk)

    if not doc.pdf_file:
        raise Http404("PDF file not found.")

    # Open the file and return a FileResponse
    return FileResponse(doc.pdf_file.open("rb"), content_type="application/pdf")