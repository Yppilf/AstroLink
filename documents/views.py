from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, Http404, FileResponse
from astrolink.views import generic_list_view, generic_list_data, generic_form_view, generic_delete_view
from .models import DocumentTemplate, TemplateField, TemplateAsset, GeneratedDocument, IgnoredDocument
from .forms import DocumentTemplateForm, TemplateFieldForm, TemplateAssetForm
from permissions.utils import external_user_permissions_required, has_permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

@external_user_permissions_required('read_documenttemplate')
def template_list(request):
    queryset = DocumentTemplate.objects.all()

    return generic_list_view(
        request,
        queryset,
        object_name="Templates",
        url_prefix="template",
        columns=["name", "description", "created_at"],
        namespace="documents",
    )

@external_user_permissions_required('read_documenttemplate')
def template_list_data(request):
    queryset = DocumentTemplate.objects.all()

    return generic_list_data(
        request,
        queryset,
        object_name="Templates",
        url_prefix="template",
        columns=["name", "description", "created_at"],
        namespace="documents",
    )

@external_user_permissions_required('create_documenttemplate')
def template_create(request):
    return generic_form_view(
        request,
        form_class=DocumentTemplateForm,
        instance=None,
        form_title="Create Template",
        url_prefix="template",
        success_message="Template created successfully",
        namespace="documents",
    )

@external_user_permissions_required('read_documenttemplate', 'update_documenttemplate')
def template_update(request, pk):
    instance = get_object_or_404(DocumentTemplate, pk=pk)

    return generic_form_view(
        request,
        form_class=DocumentTemplateForm,
        instance=instance,
        form_title="Edit Template",
        url_prefix="template",
        success_message="Template updated successfully",
        namespace="documents",
    )

@external_user_permissions_required('delete_documenttemplate')
def template_delete(request, pk):
    instance = get_object_or_404(DocumentTemplate, pk=pk)

    return generic_delete_view(
        request,
        instance,
        object_name="Template",
        url_prefix="template",
        namespace="documents",
    )

@external_user_permissions_required('read_documenttemplate', 'read_templatefield', 'read_templateasset')
def template_detail(request, pk):
    template = get_object_or_404(DocumentTemplate, pk=pk)

    return render(request, "documents/detail.html", {
        "template": template,
        "fields": template.fields.all(),
        "assets": template.assets.all(),
        "form_field": TemplateFieldForm(),
        "form_asset": TemplateAssetForm(),
    })

@require_POST
@external_user_permissions_required('create_templatefield')
def add_field(request, template_id):
    template = get_object_or_404(DocumentTemplate, pk=template_id)

    form = TemplateFieldForm(request.POST)
    if form.is_valid():
        field = form.save(commit=False)
        field.template = template
        field.save()
        form.save_m2m()

        return JsonResponse({
            "success": True,
            "field": {
                "id": field.id,
                "name": field.name,
                "label": field.label,
                "type": field.field_type,
            }
        })

    return JsonResponse({
        "success": False,
        "errors": form.errors
    }, status=400)

@require_POST
@external_user_permissions_required('delete_templatefield')
def delete_field(request, field_id):
    field = get_object_or_404(TemplateField, pk=field_id)
    field.delete()
    return JsonResponse({"success": True})

@require_POST
@external_user_permissions_required('create_templateasset')
def add_asset(request, template_id):
    template = get_object_or_404(DocumentTemplate, pk=template_id)

    form = TemplateAssetForm(request.POST, request.FILES)
    if form.is_valid():
        asset = form.save(commit=False)
        asset.template = template
        asset.save()

        return JsonResponse({
            "success": True,
            "asset": {
                "id": asset.id,
                "name": asset.name,
            }
        })

    return JsonResponse({"success": False, "errors": form.errors}, status=400)

@require_POST
@external_user_permissions_required('delete_templateasset')
def delete_asset(request, asset_id):
    asset = get_object_or_404(TemplateAsset, pk=asset_id)
    asset.delete()
    return JsonResponse({"success": True})

@login_required
@require_POST
def ignore_document(request, pk):
    document = get_object_or_404(
        GeneratedDocument,
        pk=pk
    )

    IgnoredDocument.objects.get_or_create(
        user=request.user,
        document=document,
    )

    messages.success(
        request,
        "Contract removed from your profile."
    )

    url = reverse(
        "authentication:profile_detail",
        kwargs={"username": request.user.username}
    )

    return redirect(f"{url}?tab=contracts")