from django.urls import path
from . import views

app_name = "astrolink"

urlpatterns = [
    path("", views.forum_home, name="forum_home"),

    # SUPERVISORS
    path("supervisors/", views.supervisor_list, name="supervisor_list"),
    path("supervisors/<int:pk>/", views.supervisor_detail, name="supervisor_detail"),

    # PROJECTS
    path("projects/", views.project_list, name="project_list"),
    path("projects/create/", views.project_form, name="project_create"),
    path("projects/update/<int:pk>/", views.project_form, name="project_update"),
    path("projects/delete/<int:pk>/", views.project_delete, name="project_delete"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),

    # COMPANIES
    path("companies/", views.company_list, name="company_list"),
    path("companies/create/", views.company_form, name="company_create"),
    path("companies/update/<int:pk>/", views.company_form, name="company_update"),
    path("companies/delete/<int:pk>/", views.company_delete, name="company_delete"),
    path("company/<int:pk>/", views.company_detail, name="company_detail"),

    # CASE STUDIES
    path("casestudies/", views.casestudy_list, name="casestudy_list"),
    path("casestudies/create/", views.casestudy_form, name="casestudy_create"),
    path("casestudies/update/<int:pk>/", views.casestudy_form, name="casestudy_update"),
    path("casestudies/delete/<int:pk>/", views.casestudy_delete, name="casestudy_delete"),
    path("casestudies/<int:pk>/", views.casestudy_detail, name="casestudy_detail"),

    # RESEARCH GROUPS
    path("researchgroups/", views.researchgroup_list, name="researchgroup_list"),
    path("researchgroups/create/", views.researchgroup_form, name="researchgroup_create"),
    path("researchgroups/update/<int:pk>/", views.researchgroup_form, name="researchgroup_update"),
    path("researchgroups/delete/<int:pk>/", views.researchgroup_delete, name="researchgroup_delete"),
    path("researchgroups/<int:pk>/", views.researchgroup_detail, name="researchgroup_detail"),

    # REFERENCES
    path("references/", views.reference_list, name="reference_list"),
    path("references/create/", views.reference_form, name="reference_create"),
    path("references/update/<int:pk>/", views.reference_form, name="reference_update"),
    path("references/delete/<int:pk>/", views.reference_delete, name="reference_delete"),

    # APPLICATIONS
    path("applications/", views.application_list, name="application_list"),
    path("applications/create/", views.application_form, name="application_create"),
    path("applications/update/<int:pk>/", views.application_form, name="application_update"),
    path("applications/delete/<int:pk>/", views.application_delete, name="application_delete"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("applications/<int:pk>/status/", views.application_status_update, name="application_status_update")

]