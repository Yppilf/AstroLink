# Permissions Module

## Purpose

The Permissions module provides centralized authorization for the entire platform.

It extends Django's built-in authentication and permission framework by introducing:

* Role-based access control (RBAC)
* Dynamic ownership-based permissions
* Self-service ("Own Data") permissions
* View-level permission decorators
* Automated role and permission provisioning

All applications rely on this module to determine what actions users may perform and which objects they may access.

---

# Architecture Overview

The permission system is built on four layers:

1. Django Permissions
2. Django Groups (Roles)
3. Dynamic Ownership Resolution
4. View Protection Decorators

```text
User
 │
 ▼
Role (Group)
 │
 ▼
Assigned Permissions
 │
 ▼
Dynamic Ownership Checks
 │
 ▼
View Authorization
```

This design allows permissions to be granted through:

* Static role assignments
* Ownership of specific records
* Self-access permissions

without duplicating logic across applications.

---

# Core Concepts

## Roles

Roles represent platform-wide user categories.

Configured roles include:

| Role                  | Purpose                       |
| --------------------- | ----------------------------- |
| System Admin          | Platform administration       |
| Programme Coordinator | Programme management          |
| Supervisor            | Project supervision           |
| Association           | Association management        |
| Student               | Student users                 |
| Own Data              | Dynamic ownership permissions |
| External User         | Anonymous visitors            |

Each role exists both as:

* Django Group
* Authentication Role model

ensuring synchronization between user profiles and authorization.

---

# Permission Naming Convention

Permissions follow:

```text
<action>_<resource>
```

Examples:

```text
read_project
create_application
update_generateddocument
delete_company
```

Supported actions:

```text
create
read
update
delete
```

This convention is used consistently across all modules.

---

# Permission Resolution

The central permission function is:

```python
has_permission(...)
```

All authorization checks eventually pass through this function.

---

## Authentication Check

Anonymous users are treated differently.

If a user is not authenticated:

```python
External User group permissions
```

are used.

This allows limited public access if desired.

---

## Role Permissions

Authenticated users receive permissions from:

```python
user.get_all_permissions()
```

plus any permissions assigned through their role group.

```python
Supervisor
Association
Student
Coordinator
```

---

## Dynamic Permissions

Additional permissions may be injected at runtime:

```python
user._dynamic_permissions
```

This mechanism allows temporary or calculated permissions without database changes.

---

# Ownership-Based Authorization

The platform frequently requires:

```text
Users may manage their own objects,
but not other users' objects.
```

Rather than creating separate permissions for every case, ownership is evaluated dynamically.

---

## Own Data Group

The special role:

```text
Own Data
```

contains permissions that should be granted only when a user owns a resource.

Examples:

```text
update_project
update_application
update_supervisor
update_generateddocument
```

These permissions are never granted globally.

Instead they are injected when ownership is confirmed.

---

# Ownership Checkers

Ownership logic is centralized in reusable functions.

---

## owns_project()

Determines whether a supervisor owns a project.

```python
project.supervisor.user == user
```

Used for:

* Editing projects
* Deleting projects
* Managing project applications

---

## owns_case_study()

Determines whether an association owns a case study.

```python
case_study.company.association.user == user
```

Used for:

* Editing case studies
* Deleting case studies

---

## owns_company()

Determines whether an association owns a company.

```python
company.association.user == user
```

Used for:

* Editing company details
* Managing contacts
* Updating visibility settings

---

## owns_application()

Determines access to an application.

Access may be granted through:

### Student ownership

```python
application.member == user
```

### Supervisor ownership

```python
application.project.supervisor.user == user
```

### Association ownership

```python
application.case_study.company.association.user == user
```

### General association applications

```python
application.association.user == user
```

### Coordinator oversight

Programme Coordinators may access applications related to students under their responsibility.

Additional filtering ensures that only thesis-related applications are exposed.

---

## owns_application_nonstudent()

Restricted version of application ownership.

Used when student actions should be excluded.

Typical use:

```python
Application review
Application acceptance
Application rejection
```

Only supervisors and associations can review applications.

---

## owns_generated_document()

Determines document access.

Access is granted when:

### Student owns application

```python
document.application.member == user
```

and application has not expired.

### User is signer

```python
document.signers.filter(user=user)
```

This enables contract workflows.

---

# Self Access Permissions

Some views allow users to access their own profile information.

Example:

```python
profile_detail()
```

When:

```python
check_isself=True
```

the Own Data permissions are automatically added.

This allows users to:

* View profiles
* Edit personal information
* Manage personal documents

without granting broader permissions.

---

# Permission Decorator

## external_user_permissions_required()

This decorator protects views throughout the platform.

Example:

```python
@external_user_permissions_required(
    "read_project"
)
def project_list(request):
```

Before executing a view:

1. Required permissions are checked.
2. Ownership is resolved if configured.
3. Dynamic permissions are injected.
4. Access is granted or denied.

---

## Ownership-Aware Example

```python
@external_user_permissions_required(
    "update_project",
    object_model=Project,
    ownership_checker=owns_project
)
```

Workflow:

```text
Load Project
        │
        ▼
owns_project()
        │
        ▼
Inject Own Data permissions
        │
        ▼
Check update_project
        │
        ▼
Allow or deny access
```

---

# Permission Setup Command

## setup_permissions

The management command initializes the authorization system.

```bash
python manage.py setup_permissions
```

Responsibilities:

1. Create roles
2. Create permissions
3. Create role records
4. Assign permissions to groups

---

# Generated Permissions

Permissions are automatically created for all major models.

Examples:

```text
create_project
read_project
update_project
delete_project
```

```text
create_application
read_application
update_application
delete_application
```

```text
create_generateddocument
read_generateddocument
update_generateddocument
delete_generateddocument
```

This ensures a consistent authorization model across the platform.

---

# Role Configuration

The setup command also defines which permissions belong to each role.

Examples:

## Student

Students may:

```text
Read projects
Read case studies
Read supervisors
Create applications
Manage interests
```

Students cannot:

```text
Create projects
Review applications
Manage companies
```

---

## Supervisor

Supervisors may:

```text
Create projects
Manage references
Review applications
Create contracts
Assign document signers
```

Ownership restrictions still apply.

---

## Association

Associations may:

```text
Create companies
Create case studies
Manage research groups
Review case study applications
```

Ownership restrictions still apply.

---

## Programme Coordinator

Coordinators primarily have:

```text
Read permissions
```

plus access to:

```text
Application timelines
Student oversight
Coordinator dashboards
```

---

## System Admin

Administrators manage:

```text
Users
Roles
Documentation
Templates
Tags
Research Groups
Metrics
```

They are responsible for platform-wide administration.

---

# Security Design

The permission system follows several security principles.

## Deny by Default

Users receive no permissions unless explicitly granted.

---

## Ownership Validation

Write access requires both:

```text
Permission
+
Ownership
```

where applicable.

---

## Centralized Authorization

Permission checks are never embedded directly inside templates.

All authorization flows through:

```python
has_permission()
```

or

```python
external_user_permissions_required()
```

ensuring consistency.

---

## Separation of Concerns

Authentication is handled by:

```text
authentication app
```

Authorization is handled by:

```text
permissions app
```

This keeps user management separate from access control logic.

---

# Dependencies

## Depends On

### Authentication

Provides:

* User
* Role
* Profile models

### Astrolink

Provides:

* Project ownership
* Application ownership

### Documents

Provides:

* Document ownership
* Signer ownership

---

## Used By

Every application in the platform:

* Authentication
* Astrolink
* Documents
* Metrics
* Documentation

and any future modules requiring access control.

---

# Summary

The Permissions module is the central authorization framework for the platform. It combines Django's permission system with dynamic ownership checks, self-access permissions, and reusable decorators to provide a consistent and secure access-control model. All applications depend on this module to determine who may view, create, modify, or delete platform resources.
