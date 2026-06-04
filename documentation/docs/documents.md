# Documents Module

The Documents module provides a full lifecycle system for generating, editing, signing, and locking structured documents (e.g. contracts, forms, and agreements). Documents are generated from LaTeX-based templates with dynamic fields, can be linked to applications, and support cryptographically verifiable signatures through a Simple Electronic Signature (SES) infrastructure.

---

## Overview

The system is built around four core concepts:

- **Document Templates** — Define structure, fields, and LaTeX layout
- **Generated Documents** — Instances created from templates with filled-in data
- **Template Fields & Assets** — Define input structure and LaTeX dependencies
- **Signatures & Attestations** — Cryptographically verifiable signing system

Documents can optionally be linked to an [breadcrumb-inline:application|/documentation/applications/ ::], meaning they become part of an application workflow (e.g. project acceptance contracts or case study agreements).

---

## Document Templates

A `DocumentTemplate` defines how a document should look and which data it requires.

### Key fields

- `name` — Unique identifier of the template
- `description` — Internal description
- `latex_file` — LaTeX source used for rendering the document
- `name_template` — Optional naming pattern for generated documents
- `is_active` — Whether the template is available for use
- `created_by` — User who created the template

### Purpose

Templates define:

- Document layout (LaTeX)
- Required dynamic fields
- Optional assets (images, styles, LaTeX packages)
- Signature requirements

---

## Template Fields

A `TemplateField` defines an input variable used in a document.

### Field types

- Text
- Integer
- Float
- Date
- Choice
- Boolean
- Signature

### Key properties

- `name` — Internal key used in LaTeX placeholders
- `label` — Human-readable label
- `field_type` — Type of input
- `choices` — Optional dropdown values
- `required` — Whether field must be filled
- `default_value` — Pre-filled value
- `allowed_roles` — Restricts who can sign (for signature fields)

### Signature fields

Signature fields are special:

- They are assigned to a specific user
- They generate a **DocumentSigner**
- They result in a cryptographic **Attestation**
- They are embedded into the final PDF as signature blocks

---

## Template Assets

A `TemplateAsset` represents files required by the LaTeX template.

Examples:

- Logos
- Style files (`.sty`)
- Images used in documents

These assets are made available during LaTeX compilation via `TEXINPUTS`.

---

## Generated Documents

A `GeneratedDocument` is an instantiated document created from a template.

### Key fields

- `template` — Source template
- `context_data` — JSON data used to render the document
- `pdf_file` — Generated PDF (stored privately)
- `name` — Auto-generated filename based on template rules
- `created_by` — User who generated the document
- `application` — Optional link to an Application
- `is_locked` — Prevents further editing
- `locked_at` — Timestamp when locked
- `last_edited_at` — Last modification timestamp

---

## Document Lifecycle

### 1. Generation

A document is created using a template and a dynamic form:

- User fills in template fields
- Signature fields are mapped to users
- Context data is serialized to JSON
- LaTeX is rendered via Jinja2
- PDF is generated using `xelatex`
- A `GeneratedDocument` is stored
- Optional `DocumentSigner` entries are created

---

### 2. Editing

Documents can be edited unless locked:

- Field values can be updated
- Signature changes are tracked separately
- If content changes:
  - Signatures are reset
  - Document is fully regenerated
- If only signatures change:
  - Only signer state is updated
  - PDF is regenerated without wiping signatures

---

### 3. Locking

A document can be locked manually or automatically:

- Prevents further editing
- Typically used after final approval or full signature completion
- Once locked, content becomes immutable

---

## Signing System

The signing system ensures document integrity and traceability.

### DocumentSigner

Each signature field creates a `DocumentSigner`:

- Linked to a document and field
- Assigned to a specific user
- Tracks signing status

Fields:

- `signed` — Whether signature is completed
- `signed_at` — Timestamp of signing
- `signature_blob` — LaTeX-rendered signature block
- `signature_salt` — Used for signature generation
- `attestation` — Links to cryptographic proof

---

### Signing Flow

When a user signs a document field:

1. User triggers signing action
2. An **Attestation** is created:
   - Contains metadata (user, time, field, document)
   - Generates HMAC-based signature
3. A **signature blob** is generated for LaTeX rendering
4. `DocumentSigner` is updated
5. PDF is regenerated with embedded signature
6. Attestation is finalized

---

### Attestation

An `Attestation` is a cryptographic record of a signature.

It includes:

- Payload (name, timestamp, document ID, field name)
- Salt (for HMAC security)
- Signature hash
- Final blob hash (SHA256 of rendered signature)

This ensures signatures are:

- Tamper-evident
- Verifiable
- Linked to specific document state

---

## Signature Rendering

Signatures are embedded into LaTeX using a formatted block:

- Name
- Timestamp
- Short signature hash

---

## Application Integration

Generated documents can be linked to **Applications**.

This enables workflows such as:

- Project acceptance agreements
- Case study contracts
- General association agreements

When an application is accepted, a document template may be instantiated and linked automatically.

---

## Ignored Documents

Users can hide documents from their profile using `IgnoredDocument`.

- Prevents display in dashboards
- Does not delete the document
- User-specific exclusion only

---

## Editing Rules

- Locked documents cannot be modified
- Signature changes trigger regeneration of the PDF
- Content changes reset signatures
- Every update regenerates the PDF

---

## Security Model

The system ensures document integrity via:

- Private file storage (Not accessible through URL)
- HMAC-based attestation signatures
- SHA256 hashing of signature blobs
- Role-based signing permissions
- Template-controlled field access

---

## Summary

The Documents module provides a complete document lifecycle system:

- Template-driven document generation
- Dynamic field-based forms
- LaTeX-based PDF rendering
- Role-aware signing system
- Cryptographic signature verification
- Application-linked workflows

It is designed to support legally meaningful, structured document workflows within the platform.