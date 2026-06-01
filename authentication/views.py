from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from .forms import LoginForm, SignUpForm, AdminSignUpForm, SupervisorSignUpForm
from .models import User, Role, SupervisorProfile
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .utils import assign_role
from permissions.utils import external_user_permissions_required, has_permission
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from astrolink.dynamic_email import send_dynamic_email
from datetime import datetime

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

            TEMPLATE_ID = 5
            RECIPIENTS = user.email
            DYNAMIC_DATA = {
                'username': user.display_name(),
                'year': datetime.now().year
            }

            send_dynamic_email(RECIPIENTS, TEMPLATE_ID, DYNAMIC_DATA)

            return redirect('astrolink:forum_home')
    else:
        form = SignUpForm()
    return render(request, 'forum/generic_form.html', {'form': form, 'list_url': reverse('astrolink:forum_home') })

def supervisor_register_view(request):
    if request.method == "POST":
        form = SupervisorSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)

            supervisor_role = Role.objects.filter(name="Supervisor").first()
            if supervisor_role:
                assign_role(user, supervisor_role)

            # Set inactive for pending approval
            user.is_active = False
            user.save(update_fields=['is_active'])  # only update is_active
            
            SupervisorProfile.objects.get_or_create(user=user)

            messages.info(
                request,
                "Your account has been created and is pending approval. You will be notified once approved."
            )
            return redirect('astrolink:forum_home')
    else:
        form = SupervisorSignUpForm()

    return render(
        request,
        'forum/generic_form.html',
        {
            'form': form,
            'form_title': "Supervisor Sign Up",
            'list_url': reverse('astrolink:forum_home')
        }
    )

# --- Pending Supervisors List ---
@external_user_permissions_required("create_supervisor")
def pending_supervisors_view(request):
    """
    Renders the template for pending supervisors.
    """
    data_url = reverse("authentication:pending_supervisors_list_data")
    return render(request, "authentication/pending_supervisors.html", {
        "data_url": data_url,
        "object_name": "Supervisor",
        "columns": ["display_name", "display_email"],
        "has_actions": True,
        "can_create": False,
    })

@external_user_permissions_required("create_supervisor")
def pending_supervisors_list_data(request):
    """
    Returns JSON for pending supervisors (is_active=False)
    """
    search = request.GET.get("search", "").strip()
    page = int(request.GET.get("page", 1))
    per_page = int(request.GET.get("per_page", 10))

    # Base queryset
    qs = User.objects.filter(role__name="Supervisor", is_active=False).annotate(
        display_name=Coalesce(F("screen_name"), F("legal_name")),
        display_email=F("email")
    )

    # Search filter
    if search:
        qs = qs.filter(
            Q(display_name__icontains=search) |
            Q(display_email__icontains=search)
        )

    qs = qs.order_by("pk")

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    rows = []
    for user in page_obj:
        rows.append({
            "values": [user.display_name, user.display_email],
            "detail_url": None,
            "update_url": None,
            "delete_url": reverse("authentication:approve_supervisor", args=[user.pk])
        })

    return JsonResponse({
        "rows": rows,
        "page": page_obj.number,
        "pages": paginator.num_pages,
        "total": paginator.count,
        "has_actions": True
    })


@external_user_permissions_required("create_supervisor")
def approve_supervisor(request, user_id):
    """
    Approves a pending supervisor by activating their account.
    """
    user = get_object_or_404(User, pk=user_id, role__name="Supervisor", is_active=False)
    user.is_active = True
    user.save()
    messages.success(request, f"{user.display_name()} has been approved.")
    return redirect("authentication:pending_supervisors")

@external_user_permissions_required('create_supervisor')
def approve_supervisor(request, user_id):
    user = get_object_or_404(User, pk=user_id, role__name="Supervisor", is_active=False)
    user.is_active = True
    user.save()
    messages.success(request, f"{user.display_name()} has been approved.")

    TEMPLATE_ID = 6
    RECIPIENTS = user.email
    DYNAMIC_DATA = {
        'username': user.display_name(),
        'year': datetime.now().year
    }

    send_dynamic_email(RECIPIENTS, TEMPLATE_ID, DYNAMIC_DATA)

    return redirect("authentication:pending_supervisors")

@external_user_permissions_required('create_supervisor', 'create_student', 'create_association')
def admin_register_view(request):
    ROLE_EMAIL_TEMPLATES = {
        "Student": 5,
        "Supervisor": 6,
        "Association": 7,
        "Programme Coordinator": 11,
    }

    DEFAULT_TEMPLATE_ID = 5


    if request.method == "POST":
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data["role"]
            assign_role(user, role)

            TEMPLATE_ID = ROLE_EMAIL_TEMPLATES.get(role.name, DEFAULT_TEMPLATE_ID)
            RECIPIENTS = user.email
            DYNAMIC_DATA = {
                'username': user.display_name(),
                'year': datetime.now().year
            }
            send_dynamic_email(RECIPIENTS, TEMPLATE_ID, DYNAMIC_DATA)

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

@login_required
def user_search(request):
    role = request.GET.get("role")
    q = request.GET.get("q", "").strip()

    users = User.objects.all()

    if role:
        users = users.filter(role__name=role)

    if q:
        users = users.filter(
            Q(screen_name__icontains=q)
            | Q(legal_name__icontains=q)
        )

    results = [
        {
            "id": user.id,
            "label": user.display_name(),
        }
        for user in users[:20]
    ]

    return JsonResponse(results, safe=False)

@login_required
def supervisor_search(request):
    q = request.GET.get("q", "")

    supervisors = (
        SupervisorProfile.objects
        .filter(academic_supervisor__isnull=True)
        .select_related("user")
    )

    if q:
        supervisors = supervisors.filter(
            Q(user__screen_name__icontains=q)
            | Q(user__legal_name__icontains=q)
        )

    data = [
        {
            "id": s.pk,
            "label": s.name,
        }
        for s in supervisors[:20]
    ]

    return JsonResponse(data, safe=False)