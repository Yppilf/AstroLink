from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from .models import User, Role
from documents.models import GeneratedDocument
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .utils import PROFILE_REGISTRY, model_to_field_pairs
from .forms import UserProfileForm
from astrolink.utils import get_applications_for_user, THESIS_APPLICATION_FILTER
from permissions.utils import has_permission
from astrolink.models import Application
from documents.models import IgnoredDocument

@login_required
def my_profile(request):
    return profile_detail(request, request.user.username)

@login_required
def profile_detail(request, username):
    profile_user = get_object_or_404(User, username=username)

    role_name = profile_user.role.name if profile_user.role else None
    registry_entry = PROFILE_REGISTRY.get(role_name)

    profile = None
    if registry_entry:
        profile_model = registry_entry["model"]
        profile = profile_model.objects.filter(user=profile_user).first()

    user_fields = model_to_field_pairs(
        profile_user,
        exclude=[
            "id", "password", "last_login",
            "is_active", "is_staff", "legal_name", "username", "is_superuser"
        ]
    )

    profile_fields = []
    if profile:
        profile_fields = model_to_field_pairs(
            profile,
            exclude=["id", "user", "created_at", "updated_at", "profile_picture"]
        )

    # Inject role-specific extra context
    extra_context = {}
    if profile and registry_entry and "extra_context_fn" in registry_entry:
        extra_context = registry_entry["extra_context_fn"](profile)

    is_self = request.user.is_authenticated and request.user == profile_user
    is_programme_coordinator = has_permission(request.user, "read_student") # Can be expanded to be stricter

    show_applications_tab = False
    applications = Application.objects.none()

    if request.GET.get("tab") == "applications":
        applications = get_applications_for_user(
            request.user,
            profile_user
        )

    show_applications_tab = is_self or is_programme_coordinator

    contracts = None
    can_lock_flag = False
    if request.GET.get("tab") == "contracts" and is_self:
        contracts = (
            GeneratedDocument.objects
            .filter(signers__user=profile_user)
            .exclude(
                id__in=IgnoredDocument.objects.filter(
                    user=request.user
                ).values_list("document_id", flat=True)
            )
            .distinct()
            .order_by("-created_at")
        )

        can_lock_flag = has_permission(
            request.user,
            "update_lock_generateddocument",
        )

    return render(request, "authentication/profiles/profile_detail.html", {
        "profile_user": profile_user,
        "profile": profile,
        "role": role_name,
        "active_tab": request.GET.get("tab", "overview"),
        "user_fields": user_fields,
        "profile_fields": profile_fields,
        "applications": applications,
        "contracts": contracts,
        "is_self": is_self,
        "show_applications_tab": show_applications_tab,
        "can_lock_flag": can_lock_flag,
        **extra_context
    })

@login_required
def edit_profile(request):
    user = request.user
    role_name = user.role.name if user.role else None

    registry_entry = PROFILE_REGISTRY.get(role_name)
    profile_instance = None
    profile_form_class = None

    if registry_entry:
        profile_model = registry_entry["model"]
        profile_form_class = registry_entry["form"]
        profile_instance, _ = profile_model.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserProfileForm(request.POST, instance=user)
        profile_form = (
            profile_form_class(
                request.POST,
                request.FILES,
                instance=profile_instance
            )
            if profile_form_class
            else None
        )

        forms_valid = user_form.is_valid()
        if profile_form:
            forms_valid = forms_valid and profile_form.is_valid()

        if forms_valid:
            user_form.save()
            if profile_form:
                profile_form.save()
            return redirect("authentication:my_profile")

    else:
        user_form = UserProfileForm(instance=user)
        profile_form = (
            profile_form_class(instance=profile_instance)
            if profile_form_class
            else None
        )

    return render(
        request,
        "forum/generic_form.html",
        {
            "form": user_form,
            "extra_form": profile_form,
            "title": "Edit profile",
            "submit_text": "Save changes",
            "list_url": reverse("authentication:my_profile"),
        },
    )