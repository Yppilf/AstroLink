# AstroLink Database Design

## Overview

AstroLink uses PostgreSQL as its primary datastore.

The database stores:

* Users and profiles
* Internship opportunities
* Applications
* Generated contracts
* Signature attestations
* Metrics
* Permission configuration

The database is the authoritative source for all business-critical information.

---

# Entity Overview

```text
User
 │
 ├── StudentProfile
 ├── SupervisorProfile
 ├── AssociationProfile
 └── CoordinatorProfile

Application
 │
 ├── Project
 │
 └── CaseStudy

GeneratedDocument
 │
 ├── DocumentTemplate
 ├── DocumentSigner
 └── Attestation

RawEvent
 │
 └── HourlyAggregate
```

---

# Authentication Domain

## User

Central identity model.

Stores:

* Authentication data
* Role information
* Contact information
* Legal identity

Acts as the root entity for most relationships.

---

## Role

Defines logical user roles.

Examples:

* Student
* Supervisor
* Association
* Programme Coordinator
* System Admin

Used by both:

* Permission assignment
* Document signing restrictions

---

## StudentProfile

Student-specific information.

Examples:

* Programme data
* Student metadata

Relationship:

```text
User
 1 ─── 1 StudentProfile
```

---

## SupervisorProfile

Supervisor-specific information.

Relationship:

```text
User
 1 ─── 1 SupervisorProfile
```

---

## AssociationProfile

External organization account.

Relationship:

```text
User
 1 ─── 1 AssociationProfile
```

---

## CoordinatorProfile

Programme coordinator information.

Relationship:

```text
User
 1 ─── 1 CoordinatorProfile
```

---

# Opportunity Domain

## ResearchGroup

Represents a research group.

Can own:

* Projects
* Academic opportunities

---

## Project

Supervisor-provided project.

Relationship:

```text
Supervisor
      │
      ▼
Project
```

Applications can reference projects.

---

## Company

Represents an external organization.

Owned by:

```text
Association
      │
      ▼
Company
```

---

## CaseStudy

Company-provided opportunity.

Relationship:

```text
Company
    │
    ▼
CaseStudy
```

Applications may reference case studies.

---

## Tag

Classification metadata.

Used to categorize:

* Projects
* Case studies

---

## Reference

Supervisor references.

Used within the application process.

---

## Interest

Student interests.

Used to support matching and recommendations.

---

# Application Domain

## Application

Core business entity.

Represents a student application.

Relationships:

```text
Student
   │
   ▼
Application
   │
   ├── Project
   ├── CaseStudy
   └── Association
```

Only one target opportunity is active per application.

Applications form the basis for:

* Selection workflows
* Contract generation
* Ownership validation

---

# Document Domain

## DocumentTemplate

Stores document definitions.

Contains:

* Metadata
* LaTeX source file
* Naming rules

Relationship:

```text
DocumentTemplate
        │
        ▼
TemplateField
```

---

## TemplateField

Defines dynamic document inputs.

Supported types:

* Text
* Integer
* Float
* Date
* Boolean
* Choice
* Signature

---

## TemplateAsset

Additional files required during LaTeX compilation.

Examples:

* Logos
* Images
* Style files

---

## GeneratedDocument

Represents a rendered contract.

Contains:

* Template reference
* Context data
* Generated PDF
* Lock state
* Application linkage

Relationship:

```text
GeneratedDocument
        │
        ├── DocumentSigner
        └── Attestation
```

---

## DocumentSigner

Represents a required signature.

Stores:

* Assigned user
* Signature status
* Signature timestamp

Constraint:

```text
(document, field)
```

must be unique.

---

## Attestation

Stores cryptographic proof of signature.

Contains:

* Signature payload
* Salt
* HMAC signature
* Blob hash

Provides auditability and signature verification.

---

# Permission Domain

AstroLink uses Django permissions.

Relationships:

```text
Role
  │
  ▼
Group
  │
  ▼
Permission
```

Permissions follow:

```text
action_entity
```

Examples:

```text
read_project
update_application
delete_company
```

---

# Analytics Domain

## RawEvent

Temporary tracking event.

Stores:

* Timestamp
* User
* Section

Used for aggregation.

---

## HourlyAggregate

Aggregated analytics record.

Stores:

* Hour
* Section
* Request count
* Unique visitors

Used by dashboards.

---

## AggregationState

Stores analytics progress.

Tracks:

```text
last_aggregated_hour
```

to allow incremental aggregation.

---

# Backup Domain

The backup system does not introduce additional database entities.

Backups operate directly on PostgreSQL.

Contents include:

* Users
* Applications
* Documents
* Signatures
* Metrics

---

# Data Ownership Model

Ownership is used extensively for authorization.

Examples:

```text
Student
   │
   ▼
Application
```

```text
Supervisor
   │
   ▼
Project
```

```text
Association
   │
   ▼
Company
   │
   ▼
CaseStudy
```

```text
GeneratedDocument
        │
        ▼
DocumentSigner
        │
        ▼
User
```

Ownership relationships are used by the permission framework to grant dynamic access.

---

# Data Retention

## Permanent Data

Retained indefinitely:

* Users
* Applications
* Contracts
* Signatures
* Companies
* Projects

---

## Temporary Data

Removed automatically:

* Raw analytics events
* Temporary document previews
* Compilation artifacts

---

# Backup Considerations

The PostgreSQL database is considered the authoritative source of truth.

Backups contain:

* Business data
* Contract metadata
* Signatures
* Templates

Backups do not contain:

* Public media files
* Generated PDFs
* Static assets

Contracts can be regenerated from stored template and signature data.

---

# Summary

The AstroLink database follows a domain-oriented structure consisting of:

* Authentication
* Opportunities
* Applications
* Documents
* Permissions
* Analytics

The database serves as the authoritative source of business state, while generated artifacts such as PDFs are treated as reproducible outputs derived from persisted data.
