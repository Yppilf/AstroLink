from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from .models import User, Role
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .utils import PROFILE_REGISTRY
from .forms import UserProfileForm

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

    return render(
        request,
        "authentication/profiles/profile_detail.html",
        {
            "profile_user": profile_user,
            "profile": profile,
            "role": role_name,
            "active_tab": request.GET.get("tab", "overview"),
        },
    )

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
            "cancel_url": reverse("authentication:my_profile"),
        },
    )