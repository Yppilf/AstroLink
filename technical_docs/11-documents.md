# Documents

## Purpose

The Documents module provides a complete document lifecycle system for AstroLink. It enables administrators to define reusable document templates, generate application-specific documents, assign signatories, collect electronic signatures, and maintain an auditable record of document approval.

The system is designed around three core goals:

* Centralized document template management
* Automated document generation from structured data
* Secure electronic signature and attestation workflows

All generated documents are stored privately and protected by the platform permission system.

---

# Architecture Overview

The module consists of four major subsystems:

1. Template Management
2. Document Generation
3. Signature Workflow
4. Document Storage and Access Control

```text
Document Template
    │
    ├── Template Fields
    ├── Template Assets
    │
    ▼
Dynamic Generation Form
    │
    ▼
Generated Document
    │
    ├── PDF Output
    ├── Signers
    └── Attestations
```

---

# Template Management

Templates define the structure of documents that can be generated within the platform.

Templates are stored as LaTeX source files and rendered using Jinja templating.

## DocumentTemplate

Represents a reusable document definition.

### Fields

| Field         | Description                |
| ------------- | -------------------------- |
| name          | Unique template name       |
| description   | Human-readable explanation |
| latex_file    | Uploaded LaTeX source file |
| name_template | Dynamic naming pattern     |
| created_at    | Creation timestamp         |
| created_by    | Template creator           |
| is_active     | Availability flag          |

### Dynamic Naming

Generated documents can automatically receive names based on template fields.

Example:

```text
Registration Form - {student_name}
```

Result:

```text
Registration Form - John Doe
```

---

# Template Fields

Template fields define the data required to generate a document.

## Supported Field Types

| Type      | Purpose                   |
| --------- | ------------------------- |
| text      | Free text                 |
| integer   | Whole numbers             |
| float     | Decimal values            |
| date      | Date selection            |
| choice    | Dropdown options          |
| boolean   | True/False                |
| signature | User signature assignment |

Each field contains:

* internal field name
* display label
* validation rules
* optional default values

---

# Signature Fields

Signature fields are special because they:

* assign a platform user as signer
* generate DocumentSigner records
* participate in attestation generation
* become embedded signature blocks in generated PDFs

Role restrictions can be configured using:

```python
allowed_roles
```

Examples:

* Student signature
* Supervisor signature
* Association signature
* Coordinator signature

Only users with permitted roles may be assigned.

---

# Template Assets

Templates may require additional resources.

Examples:

* Logos
* Images
* Custom fonts
* Style files
* LaTeX packages

Assets are stored separately and injected into the LaTeX compilation environment.

```text
documents/template_assets/
```

These assets become available through the TEXINPUTS environment variable during rendering.

---

# Dynamic Form Generation

Document creation forms are generated automatically from template definitions.

No custom form implementation is required per template.

The system converts each TemplateField into a Django form field at runtime.

## Example

```text
Template Field
    ↓
Generated Form Input
```

| Template Type | Generated Form |
| ------------- | -------------- |
| text          | CharField      |
| integer       | IntegerField   |
| float         | FloatField     |
| date          | DateField      |
| choice        | ChoiceField    |
| signature     | User selector  |

This allows administrators to create entirely new document types without code changes.

---

# Document Generation

Generated documents are represented by the GeneratedDocument model.

## Stored Information

Each document contains:

* originating template
* field values
* generated PDF
* creation metadata
* signer assignments
* lock status

### Context Data

User-provided values are stored as JSON.

Example:

```json
{
  "student_name": "John Doe",
  "thesis_title": "Machine Learning",
  "supervisor": 42
}
```

This context is later used to regenerate the document if modifications occur.

---

# Rendering Pipeline

Document generation follows several stages.

## Step 1 — Form Submission

Users complete the generated form.

## Step 2 — Context Creation

Field values are converted into a serializable JSON structure.

## Step 3 — Jinja Rendering

The LaTeX template is rendered using Jinja.

Custom delimiters are used to avoid conflicts with LaTeX syntax:

```jinja
<< variable >>
```

### Available Filters

#### money

```jinja
<< amount|money >>
```

Outputs:

```text
123.45
```

#### datefmt

```jinja
<< start_date|datefmt >>
```

Outputs:

```text
15-03-2026
```

#### latex

Escapes LaTeX-sensitive characters.

---

## Step 4 — XeLaTeX Compilation

Rendered source is compiled using:

```bash
xelatex
```

Compilation output and logs are stored temporarily.

If compilation fails, the generated log file can be inspected for troubleshooting.

---

## Step 5 — PDF Storage

The resulting PDF is stored in private media storage.

The GeneratedDocument record is then created and linked to the PDF.

---

# Generated Documents

Generated documents maintain both the rendered PDF and the underlying data used to produce it.

This enables regeneration when updates occur.

## Automatic Naming

When saved, the document name is recalculated using:

```python
template.name_template
```

This keeps document names synchronized with document content.

---

# Editing Documents

Generated documents may be edited until they become locked.

## Editable State

Documents remain editable when:

```text
Not manually locked
AND
Not fully signed
```

---

## Content Changes

When document content changes:

1. Context data is updated
2. Existing signatures are removed
3. Existing attestations are removed
4. PDF is regenerated

This guarantees that signatures always correspond to the exact document version that was signed.

---

## Signer Changes

If only signer assignments change:

* Existing signatures remain valid where possible
* Signer records are synchronized
* PDF is regenerated

A full signature reset is not required.

---

# Document Locking

Documents may be manually locked.

Locking prevents further edits.

## Lock Conditions

A document becomes effectively locked when:

```text
Manually Locked
OR
Fully Signed
```

Represented by:

```python
is_locked_effective
```

Once locked:

* Content cannot be modified
* Signers cannot be changed
* Signatures remain immutable

---

# Signature System

The signature workflow is implemented using:

* DocumentSigner
* Attestation

Together these provide accountability and verification.

---

# DocumentSigner

Represents a required signature.

Each signer record links:

* Document
* Signature Field
* Assigned User

Tracks:

* signed state
* timestamp
* generated signature block
* attestation reference

Only one signer may exist per document field.

---

# Signing Workflow

When a signer approves a document:

## Step 1 — Permission Validation

The user must:

* be assigned as signer
* possess signing permissions

## Step 2 — Attestation Creation

An Attestation record is generated.

Stored payload:

```json
{
  "name": "...",
  "signed_at": "...",
  "document_id": "...",
  "field_name": "..."
}
```

---

## Step 3 — Signature Generation

A cryptographic HMAC signature is created.

Inputs include:

* signer identity
* timestamp
* document information

A unique salt is generated for every attestation.

---

## Step 4 — PDF Signature Block

A visible signature block is generated.

Example:

```text
Jane Smith
15-04-2026 14:22
A1B2C3D4E5F6
```

The final line is a shortened verification signature derived from the attestation hash.

---

## Step 5 — PDF Regeneration

The document is regenerated.

Signature blocks are inserted into the rendered PDF.

The updated PDF replaces the previous version.

---

## Step 6 — Attestation Finalization

The system stores:

* payload hash
* signature hash
* finalized state

The attestation can no longer be modified.

---

# Attestations

Attestations provide auditability.

An attestation contains:

| Field          | Purpose                          |
| -------------- | -------------------------------- |
| payload        | Signature metadata               |
| signature_salt | HMAC key material                |
| signature      | Computed signature               |
| blob_hash      | Hash of rendered signature block |
| finalized      | Tamper-protection state          |

The attestation serves as the authoritative record that a user approved a specific document version at a specific time.

---

# Preview Generation

Templates can be previewed before document creation.

The preview system:

1. Builds a temporary form
2. Substitutes placeholder values
3. Generates a temporary PDF
4. Displays the rendered output

Example placeholder:

```text
[Student Name]
```

This allows template authors to validate layout and formatting before producing actual documents.

Temporary preview files are periodically cleaned up automatically.

---

# Storage Model

## Template Storage

```text
documents/templates/
```

Contains uploaded LaTeX templates.

---

## Asset Storage

```text
documents/template_assets/
```

Contains logos, images, style files, and supporting resources.

---

## Generated Documents

```text
generated_documents/
```

Contains generated PDF output.

Generated documents use private storage and are not directly accessible through public URLs.

---

# Security Model

The document system integrates with the platform permission framework.

Access to documents is controlled using:

```python
owns_generated_document()
```

Access is granted when:

* the document belongs to the user's application
* the user is an assigned signer

Combined with:

```python
external_user_permissions_required(...)
```

This ensures that document visibility, editing, locking, and signing remain restricted to authorized participants.

---

# Design Rationale

The document subsystem exists to replace manual administrative paperwork with a structured, auditable workflow.

Benefits include:

* Consistent document generation
* Reduced administrative workload
* Centralized template management
* Secure signer assignment
* Cryptographically verifiable approvals
* Complete document lifecycle tracking

By combining LaTeX rendering, dynamic forms, role-based signer assignment, and attestations, the system provides a flexible framework capable of supporting academic agreements, registrations, approvals, and contractual workflows throughout the platform.
