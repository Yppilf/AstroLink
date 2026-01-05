from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from .models import User, Role
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.urls import reverse

@login_required
def profile_view(request):
    return render(request, "authentication/profile/profile.html", {
        "page_title": "Profile",
    })
