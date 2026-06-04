from django.urls import path
from . import views

app_name="documentation"

urlpatterns = [
    path("<str:slug>/", views.docs_page, name="docs_page"),
    path("", views.home, name="home"),
]
