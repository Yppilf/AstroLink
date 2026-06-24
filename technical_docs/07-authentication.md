# Authentication App

## Purpose

The Authentication app extends Django's built-in authentication framework and provides the identity management layer for AstroLink.

It is responsible for:

* User authentication
* User registration
* User profile management
* Password management
* Account approval workflows
* Role assignment
* User search functionality
* Role-specific profile storage

The application uses a custom User model based on Django's `AbstractBaseUser` and `PermissionsMixin`.

Authentication is performed using email addresses rather than usernames.

---

# Architecture Overview

The authentication system separates:

1. Identity (`User`)
2. Authorization (`Role`)
3. Domain-specific profile information (`BaseProfile` derivatives)

```text
Role
 │
 ▼
User
 │
 ├── StudentProfile
 ├── SupervisorProfile
 ├── AssociationProfile
 └── CoordinatorProfile
```

This separation allows a common authentication system while supporting role-specific metadata.

---

# Dependencies

The Authentication app depends on:

* Django Authentication Framework
* Django Permission Framework
* Permissions App
* Dynamic Email System
* AstroLink App

## Required External Dependency

The permissions system must be initialized before the authentication system can be used.

Roles referenced throughout the application are created and managed through the Permissions app.

---

# User Model

## User

The User model is the central identity object for AstroLink.

It replaces Django's default username-based authentication with email-based authentication.

### Authentication Fields

| Field        | Description              |
| ------------ | ------------------------ |
| email        | Primary login identifier |
| password     | Hashed password          |
| is_active    | Account enabled status   |
| is_staff     | Django admin access      |
| is_superuser | Full system access       |

### Profile Fields

| Field        | Description            |
| ------------ | ---------------------- |
| first_name   | User first name        |
| last_name    | User last name         |
| legal_name   | Generated full name    |
| screen_name  | Preferred display name |
| phone_number | Contact number         |

### Role Assignment

| Field | Description           |
| ----- | --------------------- |
| role  | Linked AstroLink role |

### System Fields

| Field    | Description                    |
| -------- | ------------------------------ |
| username | Auto-generated slug identifier |

### Business Rules

* Email addresses are unique.
* Email addresses are stored in lowercase.
* Usernames are generated automatically.
* Authentication uses email rather than username.
* Display names prioritize screen names over legal names.

### Display Name Resolution

```python
screen_name or legal_name
```

---

# Role Model

## Role

Represents an application role.

### Purpose

Provides high-level categorization of users.

Examples:

* Student
* Supervisor
* Association
* Programme Coordinator

### Notes

Roles themselves do not grant permissions.

Permissions are managed through the Permissions app.

---

# Profile Architecture

The system uses role-specific profile models.

All profile types inherit from BaseProfile.

```text
BaseProfile
 │
 ├── StudentProfile
 ├── SupervisorProfile
 ├── AssociationProfile
 └── CoordinatorProfile
```

---

# BaseProfile

Abstract parent model shared by all profile types.

## Fields

| Field      | Description                 |
| ---------- | --------------------------- |
| user       | Associated User             |
| created_at | Creation timestamp          |
| updated_at | Last modification timestamp |

---

# StudentProfile

Stores student-specific information.

## Fields

| Field           | Description          |
| --------------- | -------------------- |
| biography       | Student biography    |
| snumber         | Student number       |
| level           | Degree level         |
| study_programme | Programme enrollment |

## Supported Levels

* Bachelor
* Master
* Other

## Supported Programmes

* Astronomy
* Physics
* Applied Physics
* Other

---

# SupervisorProfile

Stores supervisor-specific information.

## Fields

| Field               | Description                    |
| ------------------- | ------------------------------ |
| biography           | Supervisor biography           |
| pnumber             | Personnel identifier           |
| profile_picture     | Uploaded profile image         |
| academic_supervisor | Optional supervising professor |

## Academic Hierarchy

The model supports PhD supervision structures.

```text
Professor
      │
      ▼
PhD Student Supervisor
```

### Helper Methods

#### is_phd_student()

Returns:

```python
True
```

when an academic supervisor is assigned.

---

# AssociationProfile

Stores association information.

## Fields

| Field           | Description             |
| --------------- | ----------------------- |
| biography       | Association description |
| website         | External website        |
| profile_picture | Association image       |

---

# CoordinatorProfile

Stores programme coordinator information.

## Fields

| Field           | Description       |
| --------------- | ----------------- |
| level           | Academic level    |
| study_programme | Managed programme |

---

# Authentication Workflow

## Login

Authentication uses email addresses.

### Process

```text
User
   │
   ▼
Enter Email + Password
   │
   ▼
authenticate()
   │
   ▼
login()
   │
   ▼
Session Created
```

### Characteristics

* Email lookup is case-insensitive.
* Sessions use Django's authentication backend.
* Existing sessions are refreshed after login.

---

## Logout

```text
User
   │
   ▼
Logout Request
   │
   ▼
Session Destroyed
```

---

# Registration Workflows

The application supports multiple registration paths.

## Student Registration

Students may self-register.

### Process

```text
Student
   │
   ▼
Registration Form
   │
   ▼
User Created
   │
   ▼
Student Role Assigned
   │
   ▼
Welcome Email Sent
```

### Default Role

```text
Student
```

---

## Supervisor Registration

Supervisor registrations require approval.

### Process

```text
Supervisor
      │
      ▼
Registration Form
      │
      ▼
User Created
      │
      ▼
Role Assigned
      │
      ▼
Account Disabled
      │
      ▼
Await Approval
```

### Characteristics

* New supervisor accounts are inactive.
* SupervisorProfile is created automatically.
* Approval is performed manually.

---

## Supervisor Approval Workflow

```text
Pending Supervisor
        │
        ▼
Administrator Review
        │
        ▼
Approve
        │
        ▼
Account Activated
        │
        ▼
Approval Email Sent
```

---

## Administrative Registration

Administrators may create:

* Students
* Supervisors
* Associations
* Programme Coordinators

### Characteristics

* Role assigned during creation.
* Welcome email sent automatically.
* No approval workflow required.

---

# Profile Management

Users may manage their own profile information.

## Editable User Fields

Examples:

* Screen name
* Email
* Phone number

## Editable Profile Fields

Dependent on profile type.

Examples:

* Biography
* Programme information
* Profile picture

---

# Profile Display System

User profiles are dynamically resolved through a registry.

## Registry Responsibilities

* Determine profile model
* Determine profile form
* Inject role-specific context

### Benefits

* Single profile page implementation
* Role-specific customization
* Reduced code duplication

---

# Password Reset Workflow

The application implements token-based password resets using Django's built-in token generator.

## Request Phase

```text
User
   │
   ▼
Submit Email
   │
   ▼
Generate Token
   │
   ▼
Send Reset Email
```

### Security Features

* Email enumeration protection
* Time-limited tokens
* Cryptographically signed reset links

The same success message is returned regardless of whether the email exists.

---

## Reset Phase

```text
Reset Link
     │
     ▼
Validate Token
     │
     ▼
Set New Password
     │
     ▼
Auto Login
```

---

# Email Integration

The Authentication app sends transactional emails during account lifecycle events.

## Registration

Recipients:

* Newly registered users

## Supervisor Approval

Recipients:

* Approved supervisors

## Password Reset

Recipients:

* Account owner

---

# Media Storage

Profile images are stored under:

```text
MEDIA_ROOT/

supervisors/<user_id>/
associations/<user_id>/
```

### Characteristics

* User-specific directories
* Automatic upload path generation
* Managed through Django FileField/ImageField

---

# Templates

The Authentication app provides templates for:

* Login
* Logout
* Registration
* Supervisor Registration
* Password Reset
* Profile Display
* Profile Editing
* Pending Supervisor Review

These templates integrate with the shared generic template framework provided by the AstroLink app.

---

# Key Design Decisions

1. Email-based authentication instead of usernames.
2. Separation of identity and profile information.
3. Role-specific profile models.
4. Permission-based authorization delegated to the Permissions app.
5. Manual supervisor approval workflow.
6. Dynamic profile rendering through a registry.
7. Django-native password reset security mechanisms.
