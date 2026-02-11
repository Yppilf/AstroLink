from .utils import has_permission

def global_permissions(request):
    user = request.user

    # Now define your permission booleans
    can_manage_applications = (
        has_permission(user, "read_application")
    )

    can_manage_companies = (
        has_permission(user, "read_company")
        and has_permission(user, "create_company2")
    )

    can_approve_supervisors = (
        has_permission(user, "create_supervisor")
    )

    return {
        "can_manage_applications": can_manage_applications,
        "can_manage_companies": can_manage_companies,
        "can_approve_supervisors": can_approve_supervisors,
    }
