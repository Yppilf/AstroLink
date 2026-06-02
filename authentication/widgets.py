from django import forms
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q

from authentication.models import User
from authentication.models import SupervisorProfile, StudentProfile, AssociationProfile, CoordinatorProfile

class ModelSearchWidget(forms.TextInput):
    template_name = "widgets/user_search_widget.html"

    class Media:
        js = ["js/user_search_widget.js"]
        css = {
            "all": ["css/user_search_widget.css"]
        }

    model = None
    search_url_name = None

    def get_queryset(self):
        """
        Override in subclasses if needed.
        """
        if self.model is None:
            return None
        return self.model.objects.all()

    def get_object(self, value):
        qs = self.get_queryset()
        if qs is None:
            return None
        return qs.filter(pk=value).first()

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["search_url"] = reverse_lazy(self.search_url_name)
        context["initial_value"] = ""

        obj = None

        if value:
            obj = self.get_object(value)

        if obj:
            context["widget"]["value"] = obj.pk

            # unified display rule
            if hasattr(obj, "user"):
                context["initial_value"] = obj.user.display_name()
            elif hasattr(obj, "display_name"):
                context["initial_value"] = obj.display_name()
            else:
                context["initial_value"] = str(obj)

        return context

def model_search_view_factory(
    model,
    base_qs=None,
    search_fields=None,
    limit=20,
):
    search_fields = search_fields or []

    def view(request):
        q = request.GET.get("q", "").strip()

        if len(q) < 2:
            return JsonResponse([], safe=False)

        qs = base_qs if base_qs is not None else model.objects.all()

        query = Q()

        for field in search_fields:
            query |= Q(**{f"{field}__icontains": q})

        qs = (
            qs.filter(query)
            .distinct()
            [:limit]
        )

        return JsonResponse(
            [
                {
                    "id": obj.pk,
                    "name": (
                        obj.display_name()
                        if hasattr(obj, "display_name")
                        else obj.user.display_name()
                    )
                }
                for obj in qs
            ],
            safe=False,
        )

    return view
    
class SupervisorSearchWidget(ModelSearchWidget):
    model = SupervisorProfile
    search_url_name = "authentication:supervisor_search"

    def get_queryset(self):
        return SupervisorProfile.objects.filter(
            user__is_active=True,
            academic_supervisor__isnull=True
        )
    
class StudentUserSearchWidget(ModelSearchWidget):
    model = User
    search_url_name = "authentication:student_user_search"

    def get_queryset(self):
        return User.objects.filter(
            is_active=True,
            role__name="Student"
        )
    
class SupervisorUserSearchWidget(ModelSearchWidget):
    model = User
    search_url_name = "authentication:supervisor_user_search"

    def get_queryset(self):
        return User.objects.filter(
            is_active=True,
            role__name="Supervisor"
        )
    
class AssociationUserSearchWidget(ModelSearchWidget):
    model = User
    search_url_name = "authentication:association_user_search"

    def get_queryset(self):
        return User.objects.filter(
            is_active=True,
            role__name="Association"
        )
    
class CoordinatorUserSearchWidget(ModelSearchWidget):
    model = User
    search_url_name = "authentication:coordinator_user_search"

    def get_queryset(self):
        return User.objects.filter(
            is_active=True,
            role__name="Programme Coordinator"
        )