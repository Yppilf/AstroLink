import os
import time
import subprocess

from django.urls import reverse
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib import messages
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from django.utils import timezone
from django.core.files import File
from authentication.models import User
import datetime

from .models import DocumentTemplate, GeneratedDocument, DocumentSigner
from .forms import build_dynamic_form
from .utils import build_render_context, sync_signers

from permissions.utils import external_user_permissions_required, has_permission, owns_generated_document

def latex_escape(value):
    if value is None:
        return ""

    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }

    value = str(value)

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value

def make_json_safe(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value

def run_xelatex(tex_file_path, output_dir, env_vars):
    cmd = [
        "xelatex",
        "-interaction=nonstopmode",
        "-output-directory", output_dir,
        tex_file_path
    ]

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env_vars
    )

def generate_pdf(template, context_data, output_folder="generated", use_temp=True):
    base_dir = os.path.join(settings.PRIVATE_MEDIA_ROOT, "generated_documents")

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
        "latex": latex_escape,
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

    result = run_xelatex(tex_file_path, output_dir, env_vars)

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
                context_data[f.name] = make_json_safe(value)

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

@external_user_permissions_required(
    "update_generateddocument",
    object_model=GeneratedDocument,
    ownership_checker=owns_generated_document
)
def edit_document(request, pk):
    doc = get_object_or_404(GeneratedDocument, pk=pk)
    template = doc.template

    # Prevent editing if locked
    if doc.is_locked_effective:
        messages.error(request, "This document is locked and cannot be edited.")
        return redirect("documents:generated_document_view", pk=doc.pk)

    DynamicForm = build_dynamic_form(template)

    # Convert stored context_data → form initial values
    initial_data = doc.context_data.copy()

    for field in template.fields.all():
        if field.field_type == "signature":
            user_id = initial_data.get(field.name)
            if user_id:
                try:
                    initial_data[field.name] = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    initial_data[field.name] = None

    form = DynamicForm(request.POST or None, initial=initial_data)

    if request.method == "POST" and form.is_valid():
        raw_context_data = form.cleaned_data.copy()
        context_data = {}

        # Convert again (same as generate view)
        for f in template.fields.all():
            value = raw_context_data.get(f.name)

            if f.field_type == "signature" and value:
                context_data[f.name] = value.id
            else:
                context_data[f.name] = make_json_safe(value)

        # 1. Detect changes
        old_data = doc.context_data
        content_changed = False
        signature_changed = False

        for f in template.fields.all():
            old_value = old_data.get(f.name)
            new_value = context_data.get(f.name)

            if f.field_type == "signature":
                if old_value != new_value:
                    signature_changed = True
            else:
                if old_value != new_value:
                    content_changed = True

        # 2. Sync signers FIRST
        if signature_changed:
            sync_signers(doc, context_data)

        # 3. Update document context
        if content_changed:
            # Full reset (content changed → signatures invalid)
            doc.update_context(context_data)
        else:
            # No content change → just update context safely
            doc.context_data = context_data
            doc.last_edited_at = timezone.now()
            doc.save(update_fields=["context_data", "last_edited_at"])

            # Regenerate PDF WITHOUT wiping signatures
            render_context = build_render_context(doc)
            pdf_path = generate_pdf(template, render_context, use_temp=False)

            if doc.pdf_file:
                try:
                    doc.pdf_file.delete(save=False)
                except Exception:
                    pass

            with open(pdf_path, "rb") as f:
                doc.pdf_file.save(os.path.basename(pdf_path), File(f), save=False)

            doc.save(update_fields=["pdf_file"])

        messages.success(request, "Document updated successfully.")
        return redirect("documents:generated_document_view", pk=doc.pk)

    return render(request, "documents/generate.html", {
        "template": template,
        "form": form,
        "document": doc,
        "is_edit": True,
    })

@external_user_permissions_required(
    "update_lock_generateddocument", "update_generateddocument",
    object_model=GeneratedDocument,
    ownership_checker=owns_generated_document
)
def lock_document(request, pk):
    doc = get_object_or_404(GeneratedDocument, pk=pk)

    if doc.is_locked:
        messages.warning(request, "Document is already locked.")
        return redirect("documents:generated_document_view", pk=pk)

    doc.lock()

    messages.success(request, "Document locked successfully.")
    return redirect(request.META.get("HTTP_REFERER", "documents:generated_document_view"))

@require_POST
def generate_preview(request, template_id):
    template = get_object_or_404(DocumentTemplate, pk=template_id)
    DynamicForm = build_dynamic_form(template, preview=True)

    form = DynamicForm(request.POST)

    def get_preview_value(field):
        if field.field_type == "signature":
            return f"[{field.label}]"

        if field.field_type == "date":
            return f"[{field.label}]"

        if field.field_type == "integer":
            return 0

        if field.field_type == "float":
            return 0.0

        if field.field_type == "boolean":
            return False

        if field.field_type == "choice":
            return field.choices[0] if field.choices else ""

        return f"[{field.label}]"

    if form.is_valid():
        context_data = {}

        for field in template.fields.all():
            value = form.data.get(field.name)

            if not value:
                value = get_preview_value(field)

            context_data[field.name] = value

        pdf_path = generate_pdf(
            template,
            context_data,
            output_folder="previews",
            use_temp=True
        )

        # Build URL to preview view
        query_string = urlencode({"path": pdf_path})
        pdf_url = f"{reverse('documents:preview_pdf')}?{query_string}"

        # Cleanup old previews
        cleanup_temp_previews(folder="temp")

        return JsonResponse({"pdf_url": pdf_url})

    return JsonResponse({
        "error": form.errors
    }, status=400)

def preview_pdf(request):
    file_path = request.GET.get("path")

    if not file_path:
        raise Http404("No file specified.")

    file_path = file_path.split("?")[0]

    # SECURITY: ensure path is inside PRIVATE_MEDIA_ROOT
    abs_path = os.path.abspath(file_path)
    base_dir = os.path.abspath(settings.PRIVATE_MEDIA_ROOT)

    if not abs_path.startswith(base_dir):
        raise Http404("Invalid file path.")

    if not os.path.exists(abs_path):
        raise Http404("File not found.")

    return FileResponse(open(abs_path, "rb"), content_type="application/pdf")

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