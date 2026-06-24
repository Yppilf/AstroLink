This is exactly the point where documentation should stop being a code dump and become an **architecture description**.

A future developer does **not** need 200 pages explaining every field. They need to understand:

1. What the app is responsible for.
2. What the main entities are.
3. How users interact with those entities.
4. What workflows exist.
5. Where to look when changing functionality.

For AstroLink I would create:

```text
docs/apps/astrolink.md
```

and structure it like this:

---

# AstroLink App

## Purpose

The AstroLink app is the core collaboration platform of the system.

It provides functionality for:

* Research project management
* Case study management
* Research group management
* Student interests
* Supervisor references
* Company management
* Application workflows
* Application timeline monitoring
* Shared UI components and generic CRUD infrastructure

The app serves as the primary interaction layer between students, supervisors, associations, and programme coordinators.

---

# Domain Model

The app revolves around six primary concepts:

```text
Student
    │
    ├── Interests
    │
    └── Applications
            │
            ├── Project
            ├── Case Study
            └── General Application

Supervisor
    │
    ├── Projects
    └── References

Association
    │
    └── Companies
            │
            └── Case Studies

Tags
    │
    ├── Projects
    └── Case Studies
```

---

# Models

## Tag

Provides categorization of projects and case studies.

### Fields

| Field     | Description                  |
| --------- | ---------------------------- |
| name      | Display name                 |
| slug      | URL-safe identifier          |
| is_system | Prevents deletion through UI |

### Relationships

```text
Tag
 ├── Projects
 └── Case Studies
```

---

## Project

Research opportunities offered by supervisors.

### Fields

| Field           | Description                 |
| --------------- | --------------------------- |
| title           | Project title               |
| description     | Detailed description        |
| supervisor      | Project owner               |
| time_estimate   | Estimated workload          |
| is_open         | Accepting applications      |
| created_at      | Creation timestamp          |
| last_updated_at | Last modification timestamp |

### Relationships

```text
Supervisor
    │
    ▼
Project
    │
    ├── Applications
    ├── Attachments
    └── Tags
```

### Business Rules

* Only supervisors may create projects.
* Supervisors may only modify their own projects.
* Closed projects cannot receive new applications.

---

## Company

External organizations associated with an association.

### Purpose

Companies provide case studies for students.

### Relationships

```text
Association
      │
      ▼
Company
      │
      ▼
Case Study
```

### Status Values

| Value           | Meaning                 |
| --------------- | ----------------------- |
| UNDER_CONTRACT  | Existing collaboration  |
| EXTERN_LEADS    | External Rep. lead      |
| COMMITTEE_LEADS | Board approval required |
| OTHER           | Other status            |

---

## CaseStudy

Industry-oriented assignments offered by companies.

### Characteristics

* Similar lifecycle to projects.
* Managed through associated companies.
* Supports tags and attachments.
* Can receive applications.

---

## ResearchGroup

Stores information about academic research groups.

### Purpose

Provides visibility into research opportunities.

### Fields

* Name
* Lead professor
* Contact email
* Description

---

## Interest

Student-declared areas of interest.

### Purpose

Allows students to communicate preferred research topics.

---

## Reference

Supervisor-provided references.

### Purpose

Provides publications, links, and supporting material.

---

## Attachment

Uploaded files linked to projects or case studies.

### Supported Content

* Images
* PDFs
* Documents
* Other downloadable resources

### Storage

```text
MEDIA_ROOT/
    attachments/
```

---

## Application

Central workflow entity.

Applications connect students to projects, case studies, or associations.

### Application Types

```text
Application
    ├── Project Application
    ├── Case Study Application
    └── General Application
```

### Status Flow

```text
PENDING
   │
   ├────► REJECTED
   │
   └────► ACCEPTED
                │
                ▼
          CONFIRMED
```

### Status Definitions

| Status    | Meaning                |
| --------- | ---------------------- |
| PENDING   | Awaiting review        |
| ACCEPTED  | Accepted by supervisor |
| REJECTED  | Rejected by supervisor |
| CONFIRMED | Accepted by student    |

### Business Rules

* Applications begin in PENDING state.
* Supervisors may accept or reject.
* Students may only confirm accepted applications.
* Confirmations expire after a configurable deadline.
* Accepted applications may automatically close projects or case studies.

### Deadlines

Confirmation deadlines are calculated using:

```python
accepted_at + confirmation_deadline_days
```

---

## IgnoredApplication

Stores applications hidden by users from their personal dashboard.

### Constraints

```python
unique_together = (
    "user",
    "application",
)
```

---

# Generic CRUD Framework

The AstroLink app contains reusable CRUD helpers used throughout the application.

## Generic Views

### generic_list_view

Provides:

* Table rendering
* Pagination support
* Search integration
* AJAX loading

### generic_list_data

Provides:

* Filtering
* Sorting
* Pagination
* JSON responses

### generic_form_view

Provides:

* Create operations
* Update operations
* Attachment handling
* Redirect handling

### generic_delete_view

Provides:

* Delete confirmation
* Object removal

---

# Application Workflow

## Student Application Submission

```text
Student
    │
    ▼
Select Project / Case Study
    │
    ▼
Submit Application
    │
    ▼
Status = PENDING
    │
    ▼
Notification Email Sent
```

---

## Supervisor Review

```text
Supervisor
      │
      ▼
Review Application
      │
      ├── ACCEPTED
      │       │
      │       ▼
      │   Student Confirmation
      │
      └── REJECTED
```

---

## Student Confirmation

```text
Accepted Application
       │
       ▼
Student Confirms
       │
       ▼
Status = CONFIRMED
       │
       ▼
Optional:
Close Project
Close Case Study
```

---

# Email Integration

The application workflow triggers automated notifications.

## New Application

Recipients:

* Project supervisor
* Academic supervisor (optional)

## Application Reviewed

Recipients:

* Applicant

---

# Timeline Dashboard

The application timeline provides programme coordinators with visibility into ongoing application activity.

## Supported Filters

* Student
* Supervisor
* Project
* Case Study

## Purpose

Allows monitoring of:

* Pending applications
* Acceptances
* Rejections
* Confirmations
* Expired confirmations

---

# Templates

The AstroLink app also provides shared templates used throughout the system.

Examples include:

* Generic lists
* Generic forms
* Generic delete confirmations
* Application pages
* Project pages
* Case study pages
* Timeline views

## Note: Changes to generic templates may affect multiple apps simultaneously.

