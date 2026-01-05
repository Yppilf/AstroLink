from django.urls import resolve, reverse, Resolver404

AUTH_BREADCRUMBS = {
    "my_profile": [
        {"title": "Profile"}
    ],
    "edit_profile": [
        {"title": "Profile", "url": "authentication:my_profile"},
        {"title": "Edit"}
    ],
    "profile_detail": [
        {"title": "Profile"},
        {"title": "{username}"}
    ],
    "login": [
        {"title": "Login"}
    ],
    "register": [
        {"title": "Register"}
    ],
    "admin_register": [
        {"title": "Admin Register"}
    ],
    "password_reset_request": [
        {"title": "Forgot password"}
    ],
    "password_reset_confirm": [
        {"title": "Reset password"}
    ],
}

def dynamic_breadcrumbs(request):
    breadcrumbs = []

    try:
        match = resolve(request.path_info)
        url_name = match.url_name
        app_name = match.app_name
        kwargs = match.kwargs
    except Resolver404:
        return {"breadcrumbs": breadcrumbs}

    # --- AUTH / SPECIAL CASES ---
    if app_name == "authentication" and url_name in AUTH_BREADCRUMBS:
        for crumb in AUTH_BREADCRUMBS[url_name]:
            title = crumb["title"]

            # Replace placeholders
            if "{username}" in title:
                title = title.format(username=kwargs.get("username"))

            url = None
            if "url" in crumb:
                url = reverse(crumb["url"])

            breadcrumbs.append({
                "title": title,
                "url": url
            })

        return {"breadcrumbs": breadcrumbs}

    # --- GENERIC ASTROLINK CRUD LOGIC ---
    if url_name:
        parts = url_name.split("_")
        if len(parts) >= 2:
            model = parts[0]
            action = parts[1]

            model_title = model.replace("_", " ").title()
            list_url_name = f"{app_name}:{model}_list"

            # Add list breadcrumb
            try:
                breadcrumbs.append({
                    "title": f"{model_title}",
                    "url": reverse(list_url_name)
                })
            except:
                breadcrumbs.append({
                    "title": f"Astrolink"
                })

            if action in ("detail", "update", "delete"):
                obj_title = None
                pk = kwargs.get("pk")

                try:
                    from astrolink import models
                    model_class = getattr(models, model.capitalize())
                    obj = model_class.objects.get(pk=pk)
                    obj_title = str(obj)
                except Exception:
                    obj_title = pk

                breadcrumbs.append({"title": obj_title})

            elif action == "create":
                breadcrumbs.append({"title": f"Create {model_title}"})

    return {"breadcrumbs": breadcrumbs}

