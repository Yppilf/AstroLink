from django.urls import path
from . import views
from . import backup_views

app_name = "astrolink"

urlpatterns = [
    path("", views.forum_home, name="forum_home"),

    # SUPERVISORS
    path("supervisors/", views.supervisor_list, name="supervisor_list"),
    path("supervisors/<int:pk>/", views.supervisor_detail, name="supervisor_detail"),
    path("supervisors/data/", views.supervisor_list_data, name="supervisor_list_data"),

    # PROJECTS
    path("projects/", views.project_list, name="project_list"),
    path("projects/create/", views.project_form, name="project_create"),
    path("projects/update/<int:pk>/", views.project_form, name="project_update"),
    path("projects/delete/<int:pk>/", views.project_delete, name="project_delete"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/data/", views.project_list_data ,name="project_list_data"),

    # COMPANIES
    path("companies/", views.company_list, name="company_list"),
    path("companies/create/", views.company_create_form, name="company_create"),
    path("companies/update/<int:pk>/", views.company_form, name="company_update"),
    path("companies/delete/<int:pk>/", views.company_delete, name="company_delete"),
    path("companies/<int:pk>/", views.company_detail, name="company_detail"),
    path("companies/data/", views.company_list_data ,name="company_list_data"),

    # CASE STUDIES
    path("casestudies/", views.casestudy_list, name="casestudy_list"),
    path("casestudies/create/", views.casestudy_create_form, name="casestudy_create"),
    path("casestudies/update/<int:pk>/", views.casestudy_form, name="casestudy_update"),
    path("casestudies/delete/<int:pk>/", views.casestudy_delete, name="casestudy_delete"),
    path("casestudies/<int:pk>/", views.casestudy_detail, name="casestudy_detail"),
    path("casestudies/data/", views.casestudy_list_data, name="casestudy_list_data"),

    # RESEARCH GROUPS
    path("researchgroups/", views.researchgroup_list, name="researchgroup_list"),
    path("researchgroups/create/", views.researchgroup_form, name="researchgroup_create"),
    path("researchgroups/update/<int:pk>/", views.researchgroup_form, name="researchgroup_update"),
    path("researchgroups/delete/<int:pk>/", views.researchgroup_delete, name="researchgroup_delete"),
    path("researchgroups/<int:pk>/", views.researchgroup_detail, name="researchgroup_detail"),
    path("researchgroups/data/", views.researchgroup_list_data, name="researchgroup_list_data"),

    # REFERENCES
    path("references/", views.reference_list, name="reference_list"),
    path("references/create/", views.reference_form, name="reference_create"),
    path("references/update/<int:pk>/", views.reference_form, name="reference_update"),
    path("references/delete/<int:pk>/", views.reference_delete, name="reference_delete"),

    # INTERESTS
    path("interests/", views.interest_list, name="interest_list"),
    path("interests/create/", views.interest_form, name="interest_create"),
    path("interests/update/<int:pk>/", views.interest_form, name="interest_update"),
    path("interests/delete/<int:pk>/", views.interest_delete, name="interest_delete"),

    # APPLICATIONS
    path("applications/", views.application_list, name="application_list"),
    path("applications/create/", views.application_form, name="application_create"),
    path("applications/update/<int:pk>/", views.application_form, name="application_update"),
    path("applications/delete/<int:pk>/", views.application_delete, name="application_delete"),
    path("applications/timeline/", views.application_timeline, name="application_timeline"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("applications/<int:pk>/status/", views.application_status_update, name="application_status_update"),
    path("applications/data/", views.application_list_data, name="application_list_data"),
    path("applications/<int:pk>/ignore/", views.ignore_application, name="ignore_application"),

    # TAGS
    path("tags/", views.tag_list, name="tag_list"),
    path("tags/data/", views.tag_list_data, name="tag_list_data"),
    path("tags/create/", views.tag_form, name="tag_create"),
    path("tags/<int:pk>/edit/", views.tag_form, name="tag_update"),
    path("tags/<int:pk>/delete/", views.tag_delete, name="tag_delete"),

    path("backup/", backup_views.backup_page, name="backup_page"),
    path("backup/export/", backup_views.export_encrypted_backup, name="export_backup"),
    path("backup/import/", backup_views.import_encrypted_backup, name="import_backup"),

    path("render-preview/", views.render_preview, name="render_preview"),

    # STUDENTS
    path("students/", views.student_list, name="student_list"),
    path("students/data/", views.student_list_data, name="student_list_data"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),

    # COORDINATORS
    path("coordinators/", views.coordinator_list, name="coordinator_list"),
    path("coordinators/update/<int:pk>/", views.coordinator_form, name="coordinator_update"),
    path("coordinators/<int:pk>/", views.coordinator_detail, name="coordinator_detail"),
    path("coordinators/data/", views.coordinator_list_data, name="coordinator_list_data"),

    # ATTACHMENTS
    path("attachments/<int:pk>/delete/", views.attachment_delete, name="attachment_delete"),
]