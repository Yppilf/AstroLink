from django.contrib.auth.models import Group
import logging
from functools import wraps
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden
from authentication.models import User

logger = logging.getLogger('core.permissions')


def has_permission(user, permission, target_user=None, check_isself=False):
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
            own_data_permissions = own_data_group.permissions.values_list("codename", flat=True)
            user_permissions.update(own_data_permissions)
        except Group.DoesNotExist:
            logger.warning("The 'own_data' group is not defined in the system.")

    # Check if the required permission is in the user's permissions
    return permission in user_permissions

def external_user_permissions_required(*permission_codenames, check_isself=False):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = kwargs.get("user_id")
            if user_id:
                target_user = User.objects.filter(id=user_id).first()
            elif check_isself:
                target_user = request.user
            else:
                target_user = None

            # Permission check
            for perm in permission_codenames:
                if not has_permission(
                    request.user,
                    perm,
                    target_user=target_user,
                    check_isself=check_isself,
                ):
                    logger.warning(f"User {request.user} is missing required permission: {perm}")
                    return HttpResponseForbidden(render_to_string("forum/403.html", request=request))


            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator