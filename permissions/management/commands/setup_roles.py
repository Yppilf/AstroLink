from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from astrolink.models import Reference, Interest, Project, Company, CaseStudy, ResearchGroup, Application
from authentication.models import Role, User, SupervisorProfile, StudentProfile, AssociationProfile

class Command(BaseCommand):
    help = 'Set up roles and permissions'

    def handle(self, *args, **kwargs):
        # Define roles
        permission_map = {}
        roles = ['System Admin', 
                 'Supervisor',
                 'Association',
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
            ('user', User, ["create", "read", "update", "delete"]),
            ('supervisor', SupervisorProfile, ["create", "read", "update", "delete"]),
            ('student', StudentProfile, ["create", "read", "update", "delete"]),
            ('association', AssociationProfile, ["create", "read", "update", "delete"]),
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
                    defaults={'name': name}
                )

                permission_map[codename] = permission

                if created:
                    self.stdout.write(f"Created permission: {name}")
                else:
                    self.stdout.write(f"Permission already exists: {name}")

        # Define role-permission mappings
        role_permissions = {
            'System Admin': [
                'create_supervisor', 'read_supervisor', 'update_supervisor', 'delete_supervisor',
                'create_student', 'read_student', 'update_student', 'delete_student',
                'create_association', 'read_association', 'update_association', 'delete_association',
                'read_reference',
                'read_interest',
                'read_project',
                'read_casestudy',
                'create_researchgroup', 'read_researchgroup', 'update_researchgroup', 'delete_researchgroup',
            ], 
            'Supervisor': [
                'read_supervisor', 
                'read_student',
                'read_association',
                'read_reference', 
                'read_project', 
                'read_company',
                'read_casestudy',
                'read_researchgroup',
            ],  
            'Association': [
                'read_supervisor',
                'read_student',
                'read_association', 
                'read_interest',
                'read_reference',
                'read_project',
                'create_company', 'read_company', 
                'create_company2', 
                'create_casestudy', 'read_casestudy',
                'read_researchgroup',

                'create_researchgroup', 'update_researchgroup', 'delete_researchgroup',
            ],  
            'Own Data': [ 
                'read_user',
                
                # For Students
                'read_student', 'update_student',
                'read_application',

                # For Associations
                'update_association',
                'read_application', 'update_application',
                'update_company', 'delete_company',
                'read_company2', 'update_company2', 'delete_company2',
                'update_casestudy', 'delete_casestudy',

                # For Supervisors
                'update_supervisor',
                'create_reference', 'update_reference', 'delete_reference',
                'create_project', 'update_project', 'delete_project',
                'read_application', 'update_application',
            ],
            'Student': [
                'read_supervisor',
                'read_student',
                'read_association', 
                'read_reference',
                'read_interest',
                'read_project',
                'read_company',
                'read_casestudy',
                'read_researchgroup',
                'create_application', 

                'create_interest', 'update_interest', 'delete_interest',
            ],
            'External User': [
                # Non-authenticated users do not get any permissions on this website
            ],
            
        }

        for role, perms in role_permissions.items():
            group = Group.objects.get(name=role)
            group.permissions.clear()
            for perm_codename in perms:
                try:
                    permission = permission_map.get(perm_codename)
                    if permission:
                        group.permissions.add(permission)
                    else:
                        self.stdout.write(f"Warning: Permission {perm_codename} not found.")

                except Permission.DoesNotExist:
                    self.stdout.write(f"Warning: Permission {perm_codename} does not exist.")
            print(f"Assigned permissions to group: {role}")

        self.stdout.write("Permissions setup successfully.")
