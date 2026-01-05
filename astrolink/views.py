from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import (
    Project, Company, CaseStudy, ResearchGroup, Reference, Application
)
from authentication.models import SupervisorProfile
from .forms import (
    ProjectForm, CompanyForm, CaseStudyForm,
    ResearchGroupForm, ReferenceForm, ApplicationForm, ApplicationStatusForm
)
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.fields.related import ForeignKey
from django.contrib import messages
from permissions.utils import external_user_permissions_required, has_permission

# A helper that avoids repeating template logic:
def generic_list_view(
    request,
    queryset,
    object_name,
    url_prefix,
    columns=None,
    per_page=10,
    can_create=True,
    can_view=True,
    can_update=True,
    can_delete=True,
):
    search = request.GET.get("search", "").strip()

    if search and columns:
        model = queryset.model
        q_objects = Q()

        for col in columns:
            field = model._meta.get_field(col)

            if isinstance(field, ForeignKey):
                # Search on the related model's string-like field
                # We assume the related model defines __str__ based on a field named "name" or similar
                related_model = field.related_model

                # Try to guess useful text fields
                candidate_fields = ["name", "title", "email", "label"]
                for c in candidate_fields:
                    if c in [f.name for f in related_model._meta.fields]:
                        lookup = f"{col}__{c}__icontains"
                        q_objects |= Q(**{lookup: search})
                        break
                else:
                    # fallback fallback — string search unsupported directly
                    pass
            else:
                # Normal text field
                lookup = f"{col}__icontains"
                q_objects |= Q(**{lookup: search})

        queryset = queryset.filter(q_objects)

    queryset = queryset.order_by("pk")  # avoid unordered warning

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    objects = []
    for obj in page_obj:
        obj_dict = {
            "obj": obj,
            "detail_url": reverse(f"astrolink:{url_prefix}_detail", args=[obj.pk]) if can_view else None,
            "can_view": can_view,
            "can_update": can_update,
            "can_delete": can_delete,
        }
        if can_update:
            obj_dict["update_url"] = reverse(f"astrolink:{url_prefix}_update", args=[obj.pk])
        if can_delete:
            obj_dict["delete_url"] = reverse(f"astrolink:{url_prefix}_delete", args=[obj.pk])
        objects.append(obj_dict)

    create_url = reverse(f"astrolink:{url_prefix}_create") if can_create else None
    return render(request, "forum/generic_list.html", {
        "objects": objects,
        "page_obj": page_obj,
        "columns": columns,
        "object_name": object_name,
        "create_url": create_url,
        "page_title": f"{object_name} List",
        "search": search,
        "can_create": can_create,
    })

def generic_form_view(request, form_class, instance, form_title, url_prefix, form_kwargs=None, success_message=None):
    list_url = reverse(f"astrolink:{url_prefix}_list")
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        if form_kwargs:
            form = form_class(request.POST, request.FILES, instance=instance, **form_kwargs)
        else:
            form = form_class(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            form.save()

            if success_message:
                messages.success(request, success_message)

            if next_url:
                return redirect(next_url)
            return redirect(list_url)
    else:
        if form_kwargs:
            form = form_class(instance=instance, **form_kwargs)
        else:
            form = form_class(instance=instance)

    context = {
        "page_title": form_title,
        "form_title": form_title,
        "form": form,
        "list_url": list_url,
        "next": next_url,
    }
    return render(request, "forum/generic_form.html", context)

def generic_delete_view(request, instance, object_name, url_prefix):
    list_url = reverse(f"astrolink:{url_prefix}_list")
    if request.method == "POST":
        instance.delete()
        return redirect(list_url)

    context = {
        "page_title": f"Delete {object_name}",
        "object_name": object_name,
        "object": instance,
        "list_url": list_url,
    }
    return render(request, "forum/generic_confirm_delete.html", context)

# ----
# Home
# ----
@external_user_permissions_required("read_supervisor")
def forum_home(request):
    return render(request, "forum/forum_homepage.html")

# -----------------------------------------------
# SUPERVISOR CRUD
# -----------------------------------------------
@external_user_permissions_required("read_supervisor")
def supervisor_list(request):
    # For now, make it such that it acts as a generic list view. Only authenticated supervisors can edit their own profiles
    can_create = False
    can_view = has_permission(request.user, "read_supervisor")
    can_update = False
    can_delete = False

    return generic_list_view(
        request,
        SupervisorProfile.objects.select_related("user").all(),
        "Supervisor",
        url_prefix="supervisor",
        columns=["name", "email"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("read_supervisor")
def supervisor_detail(request, pk):
    supervisor_profile = get_object_or_404(SupervisorProfile, pk=pk)
    references = supervisor_profile.references.all()
    projects = supervisor_profile.projects.all()
    
    can_create_reference = has_permission(request.user, "create_reference")
    can_update_reference = has_permission(request.user, "update_reference")
    can_delete_reference = has_permission(request.user, "delete_reference")
    
    return render(request, "forum/supervisor_detail.html", {
        "supervisor": supervisor_profile,
        "references": references,
        "projects": projects,
        "page_title": supervisor_profile.user.display_name(),
        "can_create_reference": can_create_reference,
        "can_update_reference": can_update_reference,
        "can_delete_reference": can_delete_reference
    })


# -----------------------------------------------
# PROJECT CRUD
# -----------------------------------------------
@external_user_permissions_required("read_project")
def project_list(request):
    can_create = has_permission(request.user, "create_project")
    can_view = has_permission(request.user, "read_project")
    can_update = has_permission(request.user, "update_project")
    can_delete = has_permission(request.user, "delete_roject")

    return generic_list_view(
        request,
        Project.objects.all(),
        "Project",
        url_prefix="project",
        columns=["title", "supervisor", "time_estimate", "created_at"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_project", "update_project")
def project_form(request, pk=None):
    instance = Project.objects.filter(pk=pk).first()
    return generic_form_view(
        request,
        ProjectForm,
        instance,
        "Edit Project" if instance else "Create Project",
        url_prefix="project"
    )

@external_user_permissions_required("delete_project")
def project_delete(request, pk):
    instance = get_object_or_404(Project, pk=pk)
    return generic_delete_view(request, instance, "Project", url_prefix="project")

@external_user_permissions_required("read_project", "read_supervisor")
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    return render(request, "forum/project_detail.html", {
        "project": project,
        "page_title": project.title,
    })

# -----------------------------------------------
# COMPANY CRUD
# -----------------------------------------------
@external_user_permissions_required("read_company", "read_company2")
def company_list(request):
    can_create = has_permission(request.user, "create_company")
    can_view = has_permission(request.user, "read_company")
    can_update = has_permission(request.user, "update_company")
    can_delete = has_permission(request.user, "delete_company")

    return generic_list_view(
        request,
        Company.objects.all(),
        "Company",
        url_prefix="company",
        columns=["name", "contact_name", "email", "contact_phone", "status"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_company", "create_company2", "update_company", "update_company2")
def company_form(request, pk=None):
    instance = Company.objects.filter(pk=pk).first()
    return generic_form_view(
        request,
        CompanyForm,
        instance,
        "Edit Company" if instance else "Create Company",
        url_prefix="company"
    )

@external_user_permissions_required("delete_company", "delete_company2")
def company_delete(request, pk):
    instance = get_object_or_404(Company, pk=pk)
    return generic_delete_view(request, instance, "Company", url_prefix="company")

@external_user_permissions_required("read_company")
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    case_studies = company.case_studies.all().order_by("created_at")  # newest last

    can_view = has_permission(request.user, "read_company2")
    can_create_casestudy = has_permission(request.user, "create_casestudy")
    can_edit_casestudy = has_permission(request.user, "update_casestudy")
    can_delete_casestudy = has_permission(request.user, "delete_casestudy")

    return render(request, "forum/company_detail.html", {
        "company": company,
        "case_studies": case_studies,
        "page_title": f"{company.name}",
        "can_view_contact": can_view,
        "can_create_casestudy": can_create_casestudy,
        "can_edit_casestudy": can_edit_casestudy,
        "can_delete_casestudy": can_delete_casestudy
    })

# -----------------------------------------------
# CASE STUDY CRUD
# -----------------------------------------------
@external_user_permissions_required("read_casestudy")
def casestudy_list(request):
    can_create = has_permission(request.user, "create_casestudy")
    can_view = has_permission(request.user, "read_casestudy")
    can_update = has_permission(request.user, "update_casestudy")
    can_delete = has_permission(request.user, "delete_casestudy")

    return generic_list_view(
        request,
        CaseStudy.objects.all(),
        "Case Study",
        url_prefix="casestudy",
        columns=["title", "company", "time_estimate"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_casestudy", "update_casestudy")
def casestudy_form(request, pk=None):
    instance = CaseStudy.objects.filter(pk=pk).first()
    return generic_form_view(
        request,
        CaseStudyForm,
        instance,
        "Edit Case Study" if instance else "Create Case Study",
        url_prefix="casestudy"
    )

@external_user_permissions_required("delete_casestudy")
def casestudy_delete(request, pk):
    instance = get_object_or_404(CaseStudy, pk=pk)
    return generic_delete_view(request, instance, "Case Study", url_prefix="casestudy")

@external_user_permissions_required("read_casestudy", "read_company")
def casestudy_detail(request, pk):
    case_study = get_object_or_404(CaseStudy, pk=pk)

    return render(request, "forum/casestudy_detail.html", {
        "case_study": case_study,
        "page_title": f"{case_study.title}",
    })

# -----------------------------------------------
# RESEARCH GROUP CRUD
# -----------------------------------------------
@external_user_permissions_required("read_researchgroup")
def researchgroup_list(request):
    can_create = has_permission(request.user, "create_researchgroup")
    can_view = has_permission(request.user, "read_researchgroup")
    can_update = has_permission(request.user, "update_researchgroup")
    can_delete = has_permission(request.user, "delete_researchgroup")

    return generic_list_view(
        request,
        ResearchGroup.objects.all(),
        "Research Group",
        url_prefix="researchgroup",
        columns=["name", "lead_professor", "contact_email"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_researchgroup", "update_researchgroup")
def researchgroup_form(request, pk=None):
    instance = ResearchGroup.objects.filter(pk=pk).first()
    return generic_form_view(
        request,
        ResearchGroupForm,
        instance,
        "Edit Research Group" if instance else "Create Research Group",
        url_prefix="researchgroup"
    )

@external_user_permissions_required("delete_researchgroup")
def researchgroup_delete(request, pk):
    instance = get_object_or_404(ResearchGroup, pk=pk)
    return generic_delete_view(request, instance, "Research Group", url_prefix="researchgroup")

@external_user_permissions_required("read_researchgroup")
def researchgroup_detail(request, pk):
    research_group = get_object_or_404(ResearchGroup, pk=pk)

    return render(request, "forum/researchgroup_detail.html", {
        "research_group": research_group,
        "page_title": f"{research_group.name}",
    })

# -----------------------------------------------
# REFERENCE CRUD
# -----------------------------------------------
def reference_list(request):
    return redirect("astrolink:supervisor_list")

@external_user_permissions_required("create_reference", "update_reference")
def reference_form(request, pk=None):
    instance = Reference.objects.filter(pk=pk).first()

    # try to get supervisor id: from GET (when creating) or from instance (when editing)
    supervisor_id = request.GET.get("supervisor") or (instance.supervisor.pk if instance else None)
    supervisor = None
    if supervisor_id:
        supervisor = get_object_or_404(Supervisor, pk=supervisor_id)

    return generic_form_view(
        request,
        ReferenceForm,
        instance,
        "Edit Reference" if instance else "Create Reference",
        url_prefix="reference",
        form_kwargs={"supervisor": supervisor}
    )

@external_user_permissions_required("delete_reference")
def reference_delete(request, pk):
    instance = get_object_or_404(Reference, pk=pk)
    return generic_delete_view(request, instance, "Reference", url_prefix="reference")


# -----------------------------------------------
# APPLICATION CRUD
# -----------------------------------------------
@external_user_permissions_required("read_application")
def application_list(request):
    can_create = has_permission(request.user, "create_application")
    can_view = has_permission(request.user, "read_application")
    can_update = has_permission(request.user, "update_application")
    can_delete = has_permission(request.user, "delete_application")

    return generic_list_view(
        request,
        Application.objects.all(),
        "Application",
        url_prefix="application",
        columns=["member", "status"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_application")
def application_form(request, pk=None):
    instance = Application.objects.filter(pk=pk).first()

    if instance is None:
        project_id = request.GET.get("project")
        cs_id = request.GET.get("case_study")

        instance = Application(member=request.user)

        if project_id:
            instance.project_id = project_id
        if cs_id:
            instance.case_study_id = cs_id

    return generic_form_view(
        request,
        ApplicationForm,
        instance,
        "Edit Application" if pk else "Create Application",
        url_prefix="application",
        form_kwargs={"request": request},
        success_message="Your application was submitted successfully!"
    )

@external_user_permissions_required("delete_application")
def application_delete(request, pk):
    instance = get_object_or_404(Application, pk=pk)
    return generic_delete_view(request, instance, "Application", url_prefix="application")

@external_user_permissions_required("read_application")
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)

    target = application.project or application.case_study
    target_type = (
        "Project" if application.project else
        "Case Study" if application.case_study else
        None
    )

    return render(request, "forum/application_detail.html", {
        "application": application,
        "target": target,
        "target_type": target_type,
        "page_title": f"{application.member.display_name()}",
    })

@external_user_permissions_required("update_application")
def application_status_update(request, pk):
    app = get_object_or_404(Application, pk=pk)

    if request.method == "POST":
        form = ApplicationStatusForm(request.POST, instance=app)
        if form.is_valid():
            form.save()
            messages.success(request, "Status updated successfully!")
    return redirect("astrolink:application_detail", pk=pk)