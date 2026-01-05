from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from astrolink.models import Reference, Interest, Project, Company, CaseStudy, ResearchGroup, Application
from authentication.models import Role

class Command(BaseCommand):
    help = 'Set up roles and permissions'

    def handle(self, *args, **kwargs):
        # Define roles
        roles = ['System Admin', 
                 'Supervisor',
                 'Own Data', 
                 'Student',
                 'External User', 
        ]
        for role in roles:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(f"Created group: {role}")
            else:
                self.stdout.write(f"Group already exists: {role}")

            # Create the role in your custom Role model
            role_instance, created = Role.objects.get_or_create(name=role)
            if created:
                self.stdout.write(f"Created role: {role}")
            else:
                self.stdout.write(f"Role already exists: {role}")

        # Define permissions and their respective groups
        permissions = [
            ('reference', Reference, ["create", "read", "update", "delete"]),
            ('interest', Interest, ["create", "read", "update", "delete"]),
            ('project', Project, ["create", "read", "update", "delete"]),
            ('company', Company, ["create", "read", "update", "delete"]),                 # name, description, website
            ('company2', Company, ["create", "read", "update", "delete"]),                # contact data, status
            ('casestudy', CaseStudy, ["create", "read", "update", "delete"]),
            ('researchgroup', ResearchGroup, ["create", "read", "update", "delete"]),
            ('application', Application, ["create", "read", "update", "delete"]),
        ]

        for perm_label, model, actions in permissions:
            content_type = ContentType.objects.get_for_model(model)
            for action in actions:
                codename = f"{action}_{perm_label}"
                name = f"Can {action} {perm_label.replace('_', ' ')}"
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults={'name': name}  # only set name if creating
                )

                if created:
                    self.stdout.write(f"Created permission: {name}")
                else:
                    self.stdout.write(f"Permission already exists: {name}")

        # Define role-permission mappings
        role_permissions = {
            'System Admin': [
                'create_reference', 'read_reference', 'update_reference', 'delete_reference',
                'create_interest', 'read_interest', 'update_interest', 'delete_interest',
                'create_project', 'read_project', 'update_project', 'delete_project',
                'create_company', 'read_company', 'update_company', 'delete_company',
                'create_company2', 'read_company2', 'update_company2', 'delete_company2',
                'create_casestudy', 'read_casestudy', 'update_casestudy', 'delete_casestudy',
                'create_researchgroup', 'read_researchgroup', 'update_researchgroup', 'delete_researchgroup',
                'create_application', 'read_application', 'update_application', 'delete_application',
            ], 
            'Supervisor': [
                'create_reference', 'read_reference', 'update_reference', 'delete_reference',
                'create_project', 'read_project', 'update_project', 'delete_project',
                'create_company', 'read_company', 'update_company', 'delete_company',
                'create_company2', 'read_company2', 'update_company2', 'delete_company2',
                'create_casestudy', 'read_casestudy', 'update_casestudy', 'delete_casestudy',
                'create_researchgroup', 'read_researchgroup', 'update_researchgroup', 'delete_researchgroup',
                'create_application', 'read_application', 'update_application', 'delete_application',
                # TODO
            ],  
            'Own Data': [ 
                # TODO
            ],
            'Student': [
                'create_reference', 'read_reference', 'update_reference', 'delete_reference',
                'create_interest', 'read_interest', 'update_interest', 'delete_interest',
                'create_project', 'read_project', 'update_project', 'delete_project',
                'create_company', 'read_company', 'update_company', 'delete_company',
                'create_company2', 'read_company2', 'update_company2', 'delete_company2',
                'create_casestudy', 'read_casestudy', 'update_casestudy', 'delete_casestudy',
                'create_researchgroup', 'read_researchgroup', 'update_researchgroup', 'delete_researchgroup',
                'create_application', 'read_application', 'update_application', 'delete_application',
                # TODO
            ],
            'External User': [
                'create_reference', 'read_reference', 'update_reference', 'delete_reference',
                'create_project', 'read_project', 'update_project', 'delete_project',
                'create_company', 'read_company', 'update_company', 'delete_company',
                'create_company2', 'read_company2', 'update_company2', 'delete_company2',
                'create_casestudy', 'read_casestudy', 'update_casestudy', 'delete_casestudy',
                'create_researchgroup', 'read_researchgroup', 'update_researchgroup', 'delete_researchgroup',
                'create_application', 'read_application', 'update_application', 'delete_application',
                # TODO
            ],
            
        }

        for role, perms in role_permissions.items():
            group = Group.objects.get(name=role)
            group.permissions.clear()
            for perm_codename in perms:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(f"Warning: Permission {perm_codename} does not exist.")
            print(f"Assigned permissions to group: {role}")

        self.stdout.write("Permissions setup successfully.")
