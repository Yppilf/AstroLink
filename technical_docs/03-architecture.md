# AstroLink System Architecture

## Purpose

AstroLink is a web-based internship and graduation project management platform used to manage collaborations between students, supervisors, programme coordinators, and external associations.

The system supports:

* Internship and graduation project offerings
* Student applications
* Supervisor and association workflows
* Contract generation and signing
* Metrics collection
* Backup and recovery
* Automated communication

The platform is implemented as a Django monolith with PostgreSQL as the primary datastore.

---

# Technology Stack

## Backend

* Python
* Django
* PostgreSQL
* Django ORM
* Jinja2

## Frontend

* Django Templates
* Bootstrap
* JavaScript
* Chart.js
* SweetAlert

## Document Generation

* Jinja2
* XeLaTeX
* PDF generation pipeline

## Infrastructure

* Linux
* Nginx
* Gunicorn
* PostgreSQL

## External Services

* Brevo Transactional Email API

---

# High-Level Architecture

```text
Browser
   │
   ▼
Nginx
   │
   ▼
Gunicorn
   │
   ▼
Django Application
   │
   ├── Authentication
   ├── Permissions
   ├── AstroLink Core
   ├── Documents
   ├── Metrics
   └── Email Services
   │
   ▼
PostgreSQL
```

---

# Application Modules

## Authentication

Responsible for:

* User accounts
* Roles
* User profiles
* Login and logout

Supported roles:

* Student
* Supervisor
* Association
* Programme Coordinator
* System Administrator

---

## Permissions

Responsible for:

* Permission checks
* Ownership validation
* Dynamic self-access rights
* View protection decorators

All protected views use the centralized permission framework.

---

## AstroLink Core

Contains the primary business domain:

* Projects
* Case studies
* Companies
* Applications
* Research groups
* References
* Interests

This module implements the internship and graduation workflow.

---

## Documents

Responsible for:

* Template management
* Contract generation
* PDF rendering
* Signature workflows
* Attestation storage

Uses XeLaTeX for document generation.

---

## Metrics

Responsible for:

* Usage tracking
* Aggregation
* Dashboard visualization

Tracks authenticated user navigation patterns.

---

## Backup System

Responsible for:

* Encrypted PostgreSQL exports
* Database restoration
* Disaster recovery

Backups contain database state only.

---

## Email Service

Responsible for:

* Transactional emails
* Template-based notifications
* Delivery logging
* Retry support

Implemented using Brevo.

---

# Request Lifecycle

Every request follows the same processing pipeline.

```text
HTTP Request
      │
      ▼
Authentication Middleware
      │
      ▼
Permission Validation
      │
      ▼
Business Logic
      │
      ▼
Database Access
      │
      ▼
Template Rendering
      │
      ▼
HTTP Response
```

For successful HTML requests:

```text
Response
    │
    ▼
Metrics Middleware
    │
    ▼
RawEvent Creation
```

---

# Authentication & Authorization

Authentication and authorization are separated.

## Authentication

Authentication determines:

```text
Who is the user?
```

Handled through Django authentication.

---

## Authorization

Authorization determines:

```text
What may the user do?
```

Implemented through:

* Django permissions
* Role groups
* Ownership checks
* Dynamic permissions

```text
User
  │
  ▼
Role Group
  │
  ▼
Permission Set
  │
  ▼
Ownership Validation
  │
  ▼
Access Granted
```

---

# Document Generation Pipeline

Document generation is fully data-driven.

```text
Document Template
        │
        ▼
Dynamic Form
        │
        ▼
Context Data
        │
        ▼
Jinja Rendering
        │
        ▼
LaTeX Source
        │
        ▼
XeLaTeX
        │
        ▼
PDF
        │
        ▼
GeneratedDocument
```

Generated PDFs are stored in private storage.

---

# Document Signing Pipeline

```text
Signer
   │
   ▼
Attestation Payload
   │
   ▼
HMAC Signature
   │
   ▼
Signature Blob
   │
   ▼
PDF Regeneration
   │
   ▼
Finalized Attestation
```

Every signature is cryptographically linked to its attestation record.

---

# Analytics Pipeline

```text
User Request
      │
      ▼
Metrics Middleware
      │
      ▼
RawEvent
      │
      ▼
Hourly Aggregation
      │
      ▼
HourlyAggregate
      │
      ▼
Dashboard
```

Raw events are temporary and removed after aggregation.

---

# Storage Architecture

Storage is divided into multiple domains.

## Static Files

```text
/static/
```

Contains:

* CSS
* JavaScript
* Icons
* Frontend assets

---

## Public Media

```text
/media/
```

Contains:

* Profile pictures
* User uploads

---

## Private Media

```text
/private_media/
```

Contains:

* Generated contracts
* Signed PDFs
* Temporary previews

Private files are only accessible through protected Django views.

---

# Backup Architecture

Backups contain:

* PostgreSQL database state

Backups do not contain:

* Media files
* Generated PDFs
* Static assets

Design rationale:

* Smaller backups
* Faster recovery
* Documents can be regenerated

---

# Deployment Architecture

Production deployment follows:

```text
Internet
   │
   ▼
Nginx
   │
   ▼
Gunicorn
   │
   ▼
Django
   │
   ▼
PostgreSQL
```

Supporting directories:

```text
static/
media/
private_media/
backups/
```

---

# Security Architecture

## Authentication Security

* Django authentication framework
* Session-based authentication
* CSRF protection

## Authorization Security

* Permission decorators
* Ownership validation
* Dynamic access control

## Document Security

* Private storage
* No direct URLs
* Permission-controlled access

## Signature Integrity

* HMAC signatures
* Immutable attestations
* Signature verification support

## Backup Security

* Encrypted backup files
* Database restoration confirmation
* Restricted administrator access

---

# Architectural Decisions

## Monolithic Architecture

AstroLink uses a Django monolith.

Advantages:

* Simpler deployment
* Shared authentication
* Shared database
* Reduced operational complexity

---

## Database-Centric Design

Business state is persisted primarily in PostgreSQL.

Advantages:

* Strong consistency
* Simplified backups
* Easier recovery

---

## Regeneratable Documents

Generated PDFs are considered derived artifacts.

Source data remains authoritative.

Advantages:

* Smaller backups
* Easier recovery
* Reduced storage requirements

---

## Permission-Based Security

Security decisions are centralized.

Advantages:

* Consistent authorization
* Reduced duplication
* Easier auditing
