from django.urls import path
from . import views
from . import password_reset
from . import profile_views

app_name = "authentication"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path('forgot-password/', password_reset.password_reset_request, name='password_reset_request'),
    path('reset-password/<uidb64>/<token>/', password_reset.password_reset_confirm, name='password_reset_confirm'),

    path("profile/", profile_views.profile_view, name="profile"),
]
