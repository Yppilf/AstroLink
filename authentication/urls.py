from django.urls import path
from . import views
from . import password_reset
from . import profile_views
from . import ajax_views

app_name = "authentication"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("register/supervisor", views.supervisor_register_view, name="register_supervisor"),
    path("admin/register/", views.admin_register_view, name="admin_register"),
    path('forgot-password/', password_reset.password_reset_request, name='password_reset_request'),
    path('reset-password/<uidb64>/<token>/', password_reset.password_reset_confirm, name='password_reset_confirm'),

    path("profile/", profile_views.my_profile, name="my_profile"),
    path("profile/edit", profile_views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/", profile_views.profile_detail, name="profile_detail"),

    path("delete-account/", views.delete_account, name="delete_account"),

    path("pending-supervisors/", views.pending_supervisors_view, name="pending_supervisors"),
    path("pending-supervisors/data/", views.pending_supervisors_list_data, name="pending_supervisors_list_data"),
    path("pending-supervisors/<int:user_id>/approve/", views.approve_supervisor, name="approve_supervisor"),

    path("ajax/supervisor-search/", ajax_views.supervisor_search, name="supervisor_search"),
    path("ajax/student-user-search/", ajax_views.student_user_search, name="student_user_search"),
    path("ajax/supervisor-user-search/", ajax_views.supervisor_user_search, name="supervisor_user_search"),
    path("ajax/association-user-search/", ajax_views.association_user_search, name="association_user_search"),
    path("ajax/coordinator-user-search/", ajax_views.coordinator_user_search, name="coordinator_user_search"),
]
