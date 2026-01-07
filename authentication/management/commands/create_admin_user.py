from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from authentication.forms import AdminSignUpForm
from authentication.utils import assign_role

User = get_user_model()


class Command(BaseCommand):
    help = "Creates the first administrative platform user with a selected role."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nAstroLink Admin User Setup"))
        self.stdout.write("---------------------------------------")

        # Collect user input
        data = {}
        data["email"] = input("Email: ").strip()
        data["first_name"] = input("First Name: ").strip()
        data["last_name"] = input("Last Name: ").strip()
        data["phone_number"] = input("Phone Number: ").strip()

        # Password validation
        while True:
            pwd1 = input("Password: ")
            pwd2 = input("Repeat Password: ")
            if pwd1 == pwd2:
                data["password1"] = pwd1
                data["password2"] = pwd2
                break
            self.stdout.write(self.style.ERROR("Passwords do not match. Try again."))

        # Collect role — use form to list valid roles
        form = AdminSignUpForm(data)
        roles_qs = form.fields["role"].queryset

        self.stdout.write("\nAvailable Roles:")
        for idx, role in enumerate(roles_qs, 1):
            self.stdout.write(f"{idx}. {role.name}")

        while True:
            try:
                choice = int(input("Select role number: "))
                selected_role = roles_qs[choice - 1]
                data["role"] = selected_role.pk
                break
            except Exception:
                self.stdout.write(self.style.ERROR("Invalid selection. Try again."))

        # Build final form with role included
        form = AdminSignUpForm(data)

        if not form.is_valid():
            self.stdout.write(self.style.ERROR("Error validating input:"))
            for field, errors in form.errors.items():
                for err in errors:
                    self.stdout.write(f" - {field}: {err}")
            return

        with transaction.atomic():
            user = form.save()
            assign_role(user, selected_role)
            self.stdout.write(self.style.SUCCESS(f"\nUser {user.email} created."))
            self.stdout.write(self.style.SUCCESS(f"Assigned role: {selected_role.name}"))

        self.stdout.write(self.style.SUCCESS("\n✨ Setup complete!"))
