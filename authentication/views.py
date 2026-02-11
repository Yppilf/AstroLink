from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from .forms import LoginForm, SignUpForm, AdminSignUpForm
from .models import User, Role
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .utils import assign_role
from permissions.utils import external_user_permissions_required
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect('astrolink:forum_home')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email', '').strip().lower()
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)

                user = User.objects.get(pk=user.pk)
                update_session_auth_hash(request, user)

                if next_url and url_has_allowed_host_and_scheme(
                    next_url, allowed_hosts={request.get_host()}
                ):
                    return redirect(next_url)
                return redirect('astrolink:forum_home')

            error = "Invalid email or password."
        else:
            error = None
    else:
        form = LoginForm()
        error = None

    return render(request, 'authentication/login.html', {
        'form': form,
        'title': 'Login',
        'submit_text': 'Login',
        'error': error,
    })

@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect('astrolink:forum_home')

    context = {
        'title': "Logout",
        'cancel_url': reverse('astrolink:forum_home'),
    }
    return render(request, 'authentication/logout.html', context)

def register_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Assign the default 'Student' role to the new user
            student_role = Role.objects.filter(name="Student").first()
            if student_role:
                assign_role(user, student_role)

            TEMPLATE_ID = 1
            RECIPIENTS = user.email
            DYNAMIC_DATA = {
                'member_name': user.display_name(),
            }

            # send_dynamic_email(RECIPIENTS, TEMPLATE_ID, DYNAMIC_DATA)

            return redirect('astrolink:forum_home')
    else:
        form = SignUpForm()
    return render(request, 'forum/generic_form.html', {'form': form, 'list_url': reverse('astrolink:forum_home') })

@external_user_permissions_required('create_supervisor', 'create_student', 'create_association')
def admin_register_view(request):
    if request.method == "POST":
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data["role"]
            assign_role(user, role)

            TEMPLATE_ID = 1
            RECIPIENTS = user.email
            DYNAMIC_DATA = {
                'member_name': user.display_name(),
            }

            # send_dynamic_email(RECIPIENTS, TEMPLATE_ID, DYNAMIC_DATA)

            return redirect("authentication:profile_detail", username=user.username)
    else:
        form = AdminSignUpForm()
    return render(request, 'forum/generic_form.html', {'form': form, 'list_url': reverse('astrolink:forum_home') })

@login_required
def delete_account(request):
    if request.method == "POST":
        request.user.delete()
        messages.success(request, "Your account has been successfully deleted.")
        return redirect("astrolink:forum_home")
    return redirect("authentication:profile_detail", username=request.user.username)
