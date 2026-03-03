from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import (
    Project, Company, CaseStudy, ResearchGroup, Reference, Application, Interest, Tag
)
from authentication.models import SupervisorProfile
from .forms import (
    ProjectForm, CompanyForm, CaseStudyForm,
    ResearchGroupForm, ReferenceForm, ApplicationForm, ApplicationStatusForm, InterestForm, TagForm
)
from django.core.paginator import Paginator
from django.db.models.fields.related import ForeignKey
from django.contrib import messages
from permissions.utils import external_user_permissions_required, has_permission, owns_application, owns_case_study, owns_project, owns_company, owns_application_nonstudent
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q, F
from django.db.models.functions import Coalesce

# A helper that avoids repeating template logic:
def generic_list_view(
    request,
    queryset,
    object_name,
    url_prefix,
    columns=None,
    can_create=True,
    can_view=True,
    can_update=True,
    can_delete=True,
):
    create_url = reverse(f"astrolink:{url_prefix}_create") if can_create else None

    return render(request, "forum/generic_list.html", {
        "columns": columns,
        "object_name": object_name,
        "create_url": create_url,
        "page_title": f"{object_name} List",
        "can_create": can_create,
        "has_actions": can_update or can_delete,
        "data_url": reverse(f"astrolink:{url_prefix}_list_data"),
    })

def generic_list_data(
    request,
    queryset,
    object_name,
    url_prefix,
    columns=None,
    can_view=True,
    can_update=True,
    can_delete=True,
):
    search = request.GET.get("search", "").strip()
    page = int(request.GET.get("page", 1))
    sort = request.GET.get("sort")
    order = request.GET.get("order", "asc")
    per_page = int(request.GET.get("per_page", 10))

    model = queryset.model
    annotations = {}

    # --- Annotate columns ---
    for col in columns or []:
        try:
            field = model._meta.get_field(col)
            # BaseProfile-derived FK: annotate name for filtering/sorting
            if field.is_relation and hasattr(field.related_model, "name"):
                annotations[f"{col}_name"] = Coalesce(
                    F(f"{col}__user__screen_name"), F(f"{col}__user__legal_name")
                )
            # Direct BaseProfile or user fields
            elif col == "name" and hasattr(model, "user"):
                annotations["name"] = Coalesce(F("user__screen_name"), F("user__legal_name"))
            elif col == "email" and hasattr(model, "user"):
                annotations["email"] = F("user__email")
        except Exception:
            pass

    if annotations:
        queryset = queryset.annotate(**annotations)

    # --- Filtering ---
    if search and columns:
        q_objects = Q()
        for col in columns:
            # Use annotated FK names if present
            ann_col = f"{col}_name" if f"{col}_name" in queryset.query.annotations else col
            if ann_col in queryset.query.annotations:
                q_objects |= Q(**{f"{ann_col}__icontains": search})
            else:
                try:
                    field = model._meta.get_field(col)
                    if field.is_relation:
                        # Generic FK search on str(): fallback to nothing
                        pass
                    else:
                        q_objects |= Q(**{f"{col}__icontains": search})
                except Exception:
                    pass
        queryset = queryset.filter(q_objects)

    # --- Sorting ---
    if sort and columns and sort in columns:
        ann_sort = f"{sort}_name" if f"{sort}_name" in queryset.query.annotations else sort
        sort_field = ann_sort
        if order == "desc":
            sort_field = f"-{sort_field}"
        queryset = queryset.order_by(sort_field)
    else:
        queryset = queryset.order_by("pk")

    # --- Pagination ---
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # --- Build rows ---
    rows = []
    for obj in page_obj:
        values = []
        for col in columns:
            val = getattr(obj, col, "")
            if callable(val):
                val = val()
            elif hasattr(val, "__str__"):
                val = str(val)
            values.append(val)

        row = {
            "values": values,
            "detail_url": reverse(f"astrolink:{url_prefix}_detail", args=[obj.pk]) if can_view else None,
            "update_url": reverse(f"astrolink:{url_prefix}_update", args=[obj.pk]) if can_update else None,
            "delete_url": reverse(f"astrolink:{url_prefix}_delete", args=[obj.pk]) if can_delete else None,
        }
        rows.append(row)

    return JsonResponse({
        "rows": rows,
        "page": page_obj.number,
        "pages": paginator.num_pages,
        "total": paginator.count,
        "has_actions": can_update or can_delete,
    })

def generic_form_view(request, form_class, instance, form_title, url_prefix, form_kwargs=None, success_message=None, list_url=None):
    if not list_url:
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
def forum_home(request):
    can_apply = has_permission(request.user, "create_application")
    context = {
        "page_title": "AstroLink",
        "can_apply": can_apply,
    }
    return render(request, "forum/forum_homepage.html", context)

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
        columns=["display_name", "display_email"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("read_supervisor")
def supervisor_list_data(request):
    can_view = has_permission(request.user, "read_supervisor")
    can_update = False
    can_delete = False

    qs = SupervisorProfile.objects.select_related("user").annotate(
        display_name=Coalesce(F("user__screen_name"), F("user__legal_name")),
        display_email=F("user__email")
    )

    return generic_list_data(
        request,
        qs,
        object_name="Supervisor",
        url_prefix="supervisor",
        columns=["display_name", "display_email"], 
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("read_supervisor")
def supervisor_detail(request, pk):
    supervisor_profile = get_object_or_404(SupervisorProfile, pk=pk)
    username = supervisor_profile.user.username
    return redirect("authentication:profile_detail", username=username)

# -----------------------------------------------
# PROJECT CRUD
# -----------------------------------------------
@external_user_permissions_required("read_project")
def project_list(request):
    can_create = False
    can_view = has_permission(request.user, "read_project")
    can_update = False
    can_delete = False 

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

@external_user_permissions_required("read_project")
def project_list_data(request):
    can_view = has_permission(request.user, "read_project")
    can_update = False
    can_delete = False

    return generic_list_data(
        request,
        Project.objects.all(),
        object_name="Project",
        url_prefix="project",
        columns=["title", "supervisor", "time_estimate", "created_at"],
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_project", "update_project", object_model=Project,
    ownership_checker=owns_project)
def project_form(request, pk=None):
    user_profile = getattr(request.user, "supervisorprofile", None)
    if not user_profile:
        return HttpResponseForbidden("You are not allowed to manage projects.")

    instance = Project.objects.filter(pk=pk, supervisor=user_profile).first()
    # ensures a supervisor cannot edit someone else's project

    return generic_form_view(
        request,
        ProjectForm,
        instance,
        "Edit Project" if instance else "Create Project",
        url_prefix="project",
        form_kwargs={"supervisor": user_profile}
    )

@external_user_permissions_required("delete_project", object_model=Project,
    ownership_checker=owns_project)
def project_delete(request, pk):
    user_profile = getattr(request.user, "supervisorprofile", None)
    if not user_profile:
        return HttpResponseForbidden("You are not allowed to delete projects.")

    instance = get_object_or_404(Project, pk=pk, supervisor=user_profile)
    return generic_delete_view(request, instance, "Project", url_prefix="project")

@external_user_permissions_required("read_project", "read_supervisor", object_model=Project,
    ownership_checker=owns_project)
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    can_apply = has_permission(request.user, "create_application")

    return render(request, "forum/project_detail.html", {
        "project": project,
        "can_apply": can_apply,
        "page_title": project.title,
    })

# -----------------------------------------------
# COMPANY CRUD
# -----------------------------------------------
# In the view its ensured only companies belonging to the association are retrieved so showing contact data is fine
@external_user_permissions_required("read_company")
def company_list(request):
    can_create = has_permission(request.user, "create_company")
    can_view = has_permission(request.user, "read_company")
    can_update = has_permission(request.user, "update_company")
    can_delete = has_permission(request.user, "delete_company")

    return generic_list_view(
        request,
        Company.objects.filter(
            association=request.user.associationprofile
        ),
        "Company",
        url_prefix="company",
        columns=["name", "contact_name", "email", "contact_phone", "status"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("read_company")
def company_list_data(request):
    can_view = has_permission(request.user, "read_company")
    can_update = has_permission(request.user, "update_company")
    can_delete = has_permission(request.user, "delete_company")

    qs = Company.objects.filter(
        association=request.user.associationprofile
    )

    return generic_list_data(
        request,
        qs,
        object_name="Company",
        url_prefix="company",
        columns=["name", "contact_name", "email", "contact_phone", "status"],
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required(
    "create_company",
    "create_company2",
    object_model=Company,
    ownership_checker=owns_company,
)
def company_create_form(request):
    return generic_form_view(
        request,
        CompanyForm,
        None,
        "Create Company",
        url_prefix="company",
        form_kwargs={"request": request},
    )


@external_user_permissions_required(
    "create_company",
    "create_company2",
    "update_company",
    "update_company2",
    object_model=Company,
    ownership_checker=owns_company,
)
def company_form(request, pk=None):
    instance = Company.objects.filter(pk=pk).first()
    return generic_form_view(
        request,
        CompanyForm,
        instance,
        "Edit Company" if instance else "Create Company",
        url_prefix="company",
        form_kwargs={"request": request},
    )


@external_user_permissions_required("delete_company", "delete_company2", object_model=Company,
    ownership_checker=owns_company)
def company_delete(request, pk):
    instance = get_object_or_404(Company, pk=pk)
    return generic_delete_view(request, instance, "Company", url_prefix="company")

@external_user_permissions_required("read_company", object_model=Company,
    ownership_checker=owns_company)
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    case_studies = company.case_studies.all().order_by("created_at")  # newest last

    can_view = has_permission(request.user, "read_company2", owned_object=company, ownership_checker=owns_company)
    can_create_casestudy = has_permission(request.user, "create_casestudy", owned_object=company, ownership_checker=owns_company)
    can_edit_casestudy = has_permission(request.user, "update_casestudy", owned_object=company, ownership_checker=owns_company)
    can_delete_casestudy = has_permission(request.user, "delete_casestudy", owned_object=company, ownership_checker=owns_company)

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
        columns=["title", "company_name", "time_estimate"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("read_casestudy")
def casestudy_list_data(request):
    can_view = has_permission(request.user, "read_casestudy")
    can_update = has_permission(request.user, "update_casestudy")
    can_delete = has_permission(request.user, "delete_casestudy")

    # Annotate the company name for searching/sorting
    qs = CaseStudy.objects.select_related("company").annotate(
        company_name=F("company__name")
    )

    return generic_list_data(
        request,
        qs,
        object_name="Case Study",
        url_prefix="casestudy",
        columns=["title", "company_name", "time_estimate"],  # match annotated field
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

# Because we cant check for ownership when creating
@external_user_permissions_required(
    "create_casestudy",
    object_model=CaseStudy,
    ownership_checker=owns_case_study,
)
def casestudy_create_form(request, pk=None):
    initial = {}

    company_id = request.GET.get("company")
    if company_id:
        initial["company"] = company_id

    return generic_form_view(
        request,
        CaseStudyForm,
        None,
        "Create Case Study",
        url_prefix="casestudy",
        form_kwargs={
            "request": request,
            "initial": initial,
        },
    )


@external_user_permissions_required(
    "create_casestudy",
    "update_casestudy",
    object_model=CaseStudy,
    ownership_checker=owns_case_study,
)
def casestudy_form(request, pk=None):
    instance = CaseStudy.objects.filter(pk=pk).first()

    return generic_form_view(
        request,
        CaseStudyForm,
        instance,
        "Edit Case Study" if instance else "Create Case Study",
        url_prefix="casestudy",
        form_kwargs={"request": request},
    )


@external_user_permissions_required("delete_casestudy", object_model=CaseStudy,
    ownership_checker=owns_case_study)
def casestudy_delete(request, pk):
    instance = get_object_or_404(CaseStudy, pk=pk)
    return generic_delete_view(request, instance, "Case Study", url_prefix="casestudy")

@external_user_permissions_required("read_casestudy", "read_company", object_model=CaseStudy,
    ownership_checker=owns_case_study)
def casestudy_detail(request, pk):
    case_study = get_object_or_404(CaseStudy, pk=pk)
    can_apply = has_permission(request.user, "create_application")

    return render(request, "forum/casestudy_detail.html", {
        "case_study": case_study,
        "can_apply": can_apply,
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

@external_user_permissions_required("read_researchgroup")
def researchgroup_list_data(request):
    can_view = has_permission(request.user, "read_researchgroup")
    can_update = has_permission(request.user, "update_researchgroup")
    can_delete = has_permission(request.user, "delete_researchgroup")

    qs = ResearchGroup.objects.all()

    return generic_list_data(
        request,
        qs,
        object_name="Research Group",
        url_prefix="researchgroup",
        columns=["name", "lead_professor", "contact_email"],
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
    return redirect("authentication:my_profile")

@external_user_permissions_required("create_reference", "update_reference")
def reference_form(request, pk=None):
    user_profile = getattr(request.user, "supervisorprofile", None)
    if not user_profile:
        return HttpResponseForbidden(render_to_string("forum/403.html", request=request))

    instance = Reference.objects.filter(pk=pk, supervisor=user_profile).first()
    # pk filtering ensures a supervisor cannot edit someone else's reference

    return generic_form_view(
        request,
        ReferenceForm,
        instance,
        "Edit Reference" if instance else "Create Reference",
        url_prefix="reference",
        form_kwargs={"supervisor": user_profile}
    )

@external_user_permissions_required("delete_reference")
def reference_delete(request, pk):
    user_profile = getattr(request.user, "supervisorprofile", None)
    if not user_profile:
        return HttpResponseForbidden("You are not allowed to delete references.")

    instance = get_object_or_404(Reference, pk=pk, supervisor=user_profile)
    return generic_delete_view(request, instance, "Reference", url_prefix="reference")

# -----------------------------------------------
# INTEREST CRUD
# -----------------------------------------------
def interest_list(request):
    return redirect("authentication:my_profile")

@external_user_permissions_required("create_interest", "update_interest")
def interest_form(request, pk=None):
    user_profile = getattr(request.user, "studentprofile", None)
    if not user_profile:
        return HttpResponseForbidden(
            render_to_string("forum/403.html", request=request)
        )

    instance = Interest.objects.filter(
        pk=pk, student=user_profile
    ).first()

    return generic_form_view(
        request,
        InterestForm,
        instance,
        "Edit Interest" if instance else "Add Interest",
        url_prefix="interest",
        form_kwargs={"student": user_profile}
    )

@external_user_permissions_required("delete_interest")
def interest_delete(request, pk):
    user_profile = getattr(request.user, "studentprofile", None)
    if not user_profile:
        return HttpResponseForbidden("You are not allowed to delete interests.")

    instance = get_object_or_404(
        Interest, pk=pk, student=user_profile
    )
    return generic_delete_view(
        request, instance, "Interest", url_prefix="interest"
    )


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
        columns=["member_name", "current_status"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("read_application")
def application_list_data(request):
    can_view = has_permission(request.user, "read_application")
    can_update = has_permission(request.user, "update_application")
    can_delete = has_permission(request.user, "delete_application")

    # Annotate member_name for filtering/sorting
    qs = Application.objects.select_related("member").annotate(
        member_name=Coalesce(F("member__screen_name"), F("member__legal_name")),
        current_status=F("status")  # use raw status; can also annotate human-readable if desired
    )

    return generic_list_data(
        request,
        qs,
        object_name="Application",
        url_prefix="application",
        columns=["member_name", "current_status"],  # note: matches the annotated names
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_application",object_model=Application,
    ownership_checker=owns_application)
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
        success_message="Your application was submitted successfully!",
        list_url = reverse("astrolink:forum_home"),
    )

@external_user_permissions_required("delete_application",object_model=Application,
    ownership_checker=owns_application)
def application_delete(request, pk):
    instance = get_object_or_404(Application, pk=pk)
    return generic_delete_view(request, instance, "Application", url_prefix="application")

@external_user_permissions_required("read_application", object_model=Application,
    ownership_checker=owns_application)
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)

    target = application.project or application.case_study
    target_type = (
        "Project" if application.project else
        "Case Study" if application.case_study else
        None
    )

    can_update_status = has_permission(request.user, "update_application", owned_object=application, ownership_checker=owns_application_nonstudent)

    # Fetch related applications if not general
    related_applications = []
    if application.project:
        related_applications = Application.objects.filter(
            project=application.project
        ).exclude(pk=application.pk)
    elif application.case_study:
        related_applications = Application.objects.filter(
            case_study=application.case_study
        ).exclude(pk=application.pk)

    return render(request, "forum/application_detail.html", {
        "application": application,
        "target": target,
        "target_type": target_type,
        "page_title": f"{application.member.display_name()}",
        "can_update_status": can_update_status,
        "related_applications": related_applications,
    })

@external_user_permissions_required(
    "update_application",
    object_model=Application,
    ownership_checker=owns_application,
)
def application_status_update(request, pk):
    app = get_object_or_404(Application, pk=pk)

    if request.method == "POST":
        form = ApplicationStatusForm(request.POST, instance=app)
        if form.is_valid():
            form.save()
            messages.success(request, "Status updated successfully!")
    return redirect("astrolink:application_detail", pk=pk)

# -----------------------------------------------
# TAGS CRUD
# -----------------------------------------------
@external_user_permissions_required("create_tag", "read_tag")
def tag_list(request):
    can_create = has_permission(request.user, "create_tag")
    can_view = False
    can_update = has_permission(request.user, "update_tag")
    can_delete = has_permission(request.user, "delete_tag")

    return generic_list_view(
        request,
        Tag.objects.all(),
        "Tag",
        url_prefix="tag",
        columns=["name", "slug"],
        can_create=can_create,
        can_view=can_view,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_tag", "read_tag")
def tag_list_data(request):
    can_update = has_permission(request.user, "update_tag")
    can_delete = has_permission(request.user, "delete_tag")

    return generic_list_data(
        request,
        Tag.objects.all(),
        object_name="Tag",
        url_prefix="tag",
        columns=["name", "slug"],
        can_view=False,
        can_update=can_update,
        can_delete=can_delete,
    )

@external_user_permissions_required("create_tag", "update_tag", object_model=Tag)
def tag_form(request, pk=None):
    instance = Tag.objects.filter(pk=pk).first()

    return generic_form_view(
        request,
        TagForm,
        instance,
        "Edit Tag" if instance else "Create Tag",
        url_prefix="tag",
    )

@external_user_permissions_required("delete_tag", object_model=Tag)
def tag_delete(request, pk):
    instance = get_object_or_404(Tag, pk=pk)
    return generic_delete_view(request, instance, "Tag", url_prefix="tag")
