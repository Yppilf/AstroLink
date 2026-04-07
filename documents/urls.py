from django.urls import path
from . import views
from . import generate_views
from . import signing_views

app_name = "documents"

urlpatterns = [
    path("templates/", views.template_list, name="template_list"),
    path("templates/data/", views.template_list_data ,name="template_list_data"),
    path("templates/new/", views.template_create ,name="template_create"),
    path("templates/<int:pk>/", views.template_detail, name="template_detail"),
    path("templates/<int:pk>/update/", views.template_update, name="template_update"),
    path("templates/<int:pk>/delete/", views.template_delete, name="template_delete"),

    path("templates/<int:template_id>/fields/add/", views.add_field, name="add_field"),
    path("templates/fields/<int:field_id>/delete/", views.delete_field, name="delete_field"),
    path("templates/<int:template_id>/assets/add/", views.add_asset, name="add_asset"),
    path("templates/assets/<int:asset_id>/delete/", views.delete_asset, name="delete_asset"),

    path("templates/<int:template_id>/generate/", generate_views.generate_document, name="generate_document"),
    path("templates/<int:template_id>/preview/", generate_views.generate_preview, name="generate_preview"),

    path("<int:pk>/sign/<int:field_id>/",signing_views.sign_generated_document,name="sign_generated_document"),
    path('<int:pk>/view/', generate_views.generated_document_view, name='generated_document_view'),
    path('<int:pk>/edit/', generate_views.edit_document, name='generated_document_edit'),
    path('<int:pk>/lock/', generate_views.lock_document, name='lock_document'),
]