from django.contrib.auth.models import Group
import logging
from functools import wraps
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden
from authentication.models import User
from astrolink.models import Application
from documents.models import GeneratedDocument, DocumentSigner

logger = logging.getLogger('core.permissions')

def owns_application(user, application):
    if not user.is_authenticated:
        return False

    if application.member_id == user.id:
        return True

    if application.project and application.project.supervisor:
        return application.project.supervisor.user_id == user.id

    if (
        application.case_study
        and application.case_study.company
        and application.case_study.company.association
    ):
        return application.case_study.company.association.user_id == user.id
    
    if (
        application.project is None
        and application.case_study is None
        and application.association
        and application.association.user == user
    ):
        return True

    return False

def owns_application_nonstudent(user, application):
    if not user.is_authenticated:
        return False

    if user.role == "Student":
        return False

    if application.project and application.project.supervisor:
        return application.project.supervisor.user_id == user.id

    if (
        application.case_study
        and application.case_study.company
        and application.case_study.company.association
    ):
        return application.case_study.company.association.user_id == user.id

    if (
        application.project is None
        and application.case_study is None
        and application.association
        and application.association.user == user
    ):
        return True

    return False


def owns_project(user, project):
    if not user.is_authenticated:
        return False

    return (
        project.supervisor
        and project.supervisor.user_id == user.id
    )


def owns_case_study(user, case_study):
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, "associationprofile"):
        return False

    return (
        case_study.company
        and case_study.company.association
        and case_study.company.association.user_id == user.id
    )

def owns_company(user, company):
    if not user.is_authenticated:
        return False

    return (
        company.association
        and company.association.user_id == user.id
    )

def owns_generated_document(user, document: GeneratedDocument):
    if not user.is_authenticated:
        return False
    return (
        document.application and document.application.member == user and not document.application.is_expired
    ) or document.signers.filter(user=user).exists()


def has_permission(
    user,
    permission,
    *,
    target_user=None,
    check_isself=False,
    owned_object=None,
    ownership_checker=None,
):
    """
    Check if a user has a specific permission, considering self-access if applicable.

    Args:
        user: The current user.
        permission: The permission codename to check.
        target_user: The user whose data is being accessed (optional).
        check_isself: Whether to grant permissions dynamically for self-access.

    Returns:
        bool: True if the user has the permission, False otherwise.
    """
    if not user.is_authenticated:
        external_user = Group.objects.filter(name="External User").first()
        if not external_user:
            return False
        external_permission = external_user.permissions.values_list("codename", flat=True)
        return permission in external_permission

    # Check if the user is accessing their own data
    is_self = check_isself and target_user and user.id == target_user.id

    # Fetch the user's permissions
    user_permissions = {perm.split('.')[-1] for perm in user.get_all_permissions()}

    if hasattr(user, "_dynamic_permissions"):
        user_permissions.update(user._dynamic_permissions)

    # Also inject role-group permissions if needed
    if hasattr(user, "role") and user.role:
        try:
            role_group = Group.objects.get(name=user.role)
            user_permissions.update(role_group.permissions.values_list("codename", flat=True))
        except Group.DoesNotExist:
            pass

    # Dynamically add "own_data" permissions if accessing their own data
    if is_self:
        try:
            own_data_group = Group.objects.get(name="Own Data")
            user_permissions.update(
                own_data_group.permissions.values_list("codename", flat=True)
            )
        except Group.DoesNotExist:
            logger.warning("'Own Data' group missing")

    # Object ownership
    if owned_object and ownership_checker:
        try:
            if ownership_checker(user, owned_object):
                own_data_group = Group.objects.get(name="Own Data")
                user_permissions.update(
                    own_data_group.permissions.values_list("codename", flat=True)
                )
        except Group.DoesNotExist:
            logger.warning("'Own Data' group missing")

    # Check if the required permission is in the user's permissions
    return permission in user_permissions

def external_user_permissions_required(
    *permission_codenames,
    check_isself=False,
    object_model=None,
    ownership_checker=None,
):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            # Target user (profiles)
            user_id = kwargs.get("user_id")
            target_user = (
                User.objects.filter(id=user_id).first()
                if user_id else request.user if check_isself else None
            )

            # Resolve owned object
            owned_object = None
            if object_model:
                owned_object = (
                    object_model.objects
                    .select_related()
                    .filter(pk=kwargs.get("pk"))
                    .first()
                )

            for perm in permission_codenames:
                if not has_permission(
                    request.user,
                    perm,
                    target_user=target_user,
                    check_isself=check_isself,
                    owned_object=owned_object,
                    ownership_checker=ownership_checker,
                ):
                    print(f"User {request.user} is missing permission {perm}")
                    return HttpResponseForbidden(
                        render_to_string("forum/403.html", request=request)
                    )

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
