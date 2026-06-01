from django import forms
from django.urls import reverse_lazy

from authentication.models import User
from authentication.models import SupervisorProfile

class UserSearchWidget(forms.TextInput):
    template_name = "widgets/user_search_widget.html"

    class Media:
        js = ["js/user_search_widget.js"]
        css = {"all": ["css/user_search_widget.css"]}

    search_url_name = None

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["search_url"] = reverse_lazy(self.search_url_name)
        context["initial_value"] = ""

        if value:
            try:
                supervisor = SupervisorProfile.objects.select_related("user").get(pk=value)

                context["initial_value"] = supervisor.user.display_name()

            except SupervisorProfile.DoesNotExist:
                pass

        return context
    
class SupervisorSearchWidget(UserSearchWidget):
    search_url_name = "authentication:supervisor_search"