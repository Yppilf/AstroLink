from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from astrolink.models import Reference, Interest, Project, Company, CaseStudy, ResearchGroup, Application, Tag
from authentication.models import Role, User, SupervisorProfile, StudentProfile, AssociationProfile, CoordinatorProfile
from documents.models import DocumentTemplate, TemplateField, TemplateAsset, GeneratedDocument, DocumentSigner

class Command(BaseCommand):
    help = 'Set up roles and permissions'

    def handle(self, *args, **kwargs):
        # Define roles
        permission_map = {}
        roles = ['System Admin', 
                 'Programme Coordinator',
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
            ('coordinator', CoordinatorProfile, ["create", "read", "update", "delete"]),
            ('reference', Reference, ["create", "read", "update", "delete"]),
            ('interest', Interest, ["create", "read", "update", "delete"]),
            ('project', Project, ["create", "read", "update", "delete"]),
            ('company', Company, ["create", "read", "update", "delete"]),                 # name, description, website
            ('company2', Company, ["create", "read", "update", "delete"]),                # contact data, status
            ('casestudy', CaseStudy, ["create", "read", "update", "delete"]),
            ('researchgroup', ResearchGroup, ["create", "read", "update", "delete"]),
            ('application', Application, ["create", "read", "update", "delete"]),
            ('tag', Tag, ["create", "read", "update", "delete"]),

            ('documenttemplate', DocumentTemplate, ["create", "read", "update", "delete"]),
            ('templatefield', TemplateField, ["create", "read", "update", "delete"]),
            ('templateasset', TemplateAsset, ["create", "read", "update", "delete"]),
            ('generateddocument', GeneratedDocument, ["create", "read", "update", "delete"]),   # General creation etc
            ('lock_generateddocument', GeneratedDocument, ["create", "read", "update", "delete"]),  # Locking the document
            ('documentsigner', DocumentSigner, ["create", "read", "update", "delete"]),
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
                'create_student',
                'create_association', 'read_association', 'update_association', 'delete_association',
                'create_coordinator',
                'read_reference',
                'read_interest',
                'read_project',
                'read_casestudy',
                'create_researchgroup', 'read_researchgroup', 'update_researchgroup', 'delete_researchgroup',
                'create_tag', 'read_tag', 'update_tag', 'delete_tag',

                'create_documenttemplate', 'read_documenttemplate', 'update_documenttemplate', 'delete_documenttemplate',
                'create_templatefield', 'read_templatefield', 'update_templatefield', 'delete_templatefield',
                'create_templateasset', 'read_templateasset', 'update_templateasset', 'delete_templateasset',
            ], 
            'Programme Coordinator': [
                'read_supervisor', 
                'read_student',
                'read_association',
                'read_coordinator',
                'create_reference', 'read_reference', 'update_reference',  
                'create_project', 'read_project', 'update_project',
                'read_company',
                'read_casestudy',
                'read_researchgroup',
                'read_tag',
            ],
            'Supervisor': [
                'read_supervisor', 
                # 'read_student',
                'read_association',
                'create_reference', 'read_reference', 'update_reference',  
                'create_project', 'read_project', 'update_project',
                'read_company',
                'read_casestudy',
                'read_researchgroup',
                'read_tag',

                'create_generateddocument',
                'create_documentsigner',
                'update_lock_generateddocument',    # Can lock own documents, but student cannot, so use together with update_generateddocument
            ],  
            'Association': [
                'read_supervisor',
                # 'read_student',
                'read_association', 
                'read_interest',
                'read_reference',
                'read_project',
                'create_company', 'read_company', 
                'create_company2', 
                'create_casestudy', 'read_casestudy',
                'read_researchgroup',
                'create_researchgroup', 'update_researchgroup', 'delete_researchgroup',
                'read_tag',

                'create_generateddocument',
                'update_lock_generateddocument',
                'create_documentsigner',
            ],  
            'Own Data': [ 
                'read_user',
                'read_generateddocument',
                'update_generateddocument',
                'update_documentsigner',
                
                # For Students
                'read_application',

                # For Associations
                'update_association',
                'read_application', 'update_application',
                'update_company', 'delete_company',
                'read_company2', 'update_company2', 'delete_company2',
                'update_casestudy', 'delete_casestudy',

                # For Supervisors
                'update_supervisor',
                'delete_reference',
                'delete_project',
                'read_application', 'update_application',

                # For Coordinators
                'read_application',
                'update_coordinator',
            ],
            'Student': [
                'read_supervisor',
                'read_association', 
                'read_reference',
                'read_interest',
                'read_project',
                'read_company',
                'read_casestudy',
                'read_researchgroup',
                'create_application', 
                'read_tag',
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
