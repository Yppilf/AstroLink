# Media & File Storage Architecture

## Purpose

AstroLink stores and serves several categories of files:

- Static application assets (CSS, JavaScript, images)
- Public media uploads (profile pictures, general user uploads)
- Private documents (generated contracts, signed agreements)
- Template files used for document generation
- Temporary preview files

The storage architecture intentionally separates public and private content to ensure sensitive documents cannot be accessed directly through public URLs.

---

# Storage Overview

| Storage Type | Purpose | Publicly Accessible |
|--------------|----------|---------------------|
| Static Files | CSS, JS, icons, frontend assets | Yes |
| Media Files | General user uploads | Yes |
| Private Media | Contracts, generated PDFs, sensitive documents | No |
| Temporary Generated Files | Preview rendering and LaTeX compilation output | No |

---

# Static Files

## Configuration

```python
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

if is_production:
    STATIC_ROOT = '/var/www/siriusa/static_astrolink/'
else:
    STATIC_ROOT = BASE_DIR / 'staticfiles'
```

## Purpose

Static files contain:

- CSS
- JavaScript
- Icons
- Images used by the application UI
- Third-party frontend libraries

These files are:

- Version controlled
- Deployed with the application
- Collected using Django's `collectstatic`

---

# Public Media Storage

## Configuration

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
```

## Purpose

Used for general uploaded content such as:

- Profile pictures
- Uploaded images
- Other non-sensitive media assets

Files stored here can be served directly by the web server.

---

# Private Media Storage

## Configuration

```python
PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, "private_media")
```

Custom storage backend:

```python
class PrivateMediaStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(
            location=settings.PRIVATE_MEDIA_ROOT,
            base_url=None
        )
```

## Purpose

Private storage contains sensitive files including:

- Generated contracts
- Signed documents
- Legal agreements
- Generated PDFs

Unlike normal media files:

- No public URL is generated
- Files cannot be downloaded directly
- Access must pass through Django permission checks

---

# Private Document Access

Generated documents are stored using:

```python
pdf_file = models.FileField(
    upload_to=private_upload_path,
    storage=PrivateMediaStorage()
)
```

Access occurs through protected views:

```python
generated_document_view(...)
```

The view:

1. Loads the document
2. Validates permissions
3. Verifies ownership
4. Streams the file through Django

Example:

```python
return FileResponse(
    doc.pdf_file.open("rb"),
    content_type="application/pdf"
)
```

This prevents users from bypassing authorization by guessing URLs.

---

# Document Templates

Document templates are stored as uploaded files:

```python
latex_file = models.FileField(
    upload_to=template_upload_path
)
```

Example structure:

```text
documents/
└── templates/
    └── Internship Contract/
        └── contract.tex
```

These templates are managed through the administration interface and used during PDF generation.

---

# Template Assets

Additional LaTeX resources are stored separately:

```python
file = models.FileField(
    upload_to="documents/template_assets/"
)
```

Examples:

- Logos
- Images
- Custom style files (`.sty`)
- Supporting LaTeX resources

Example:

```text
documents/
└── template_assets/
    ├── logo.png
    ├── header.png
    └── university.sty
```

During rendering, asset locations are injected into:

```python
TEXINPUTS
```

allowing XeLaTeX to locate referenced resources.

---

# Generated Documents

Generated contracts are stored under:

```text
private_media/
└── generated_documents/
```

Typical contents:

```text
generated_documents/
├── Contract_174600001.pdf
├── Contract_174600002.pdf
└── ...
```

Each file is associated with a:

```python
GeneratedDocument
```

record.

The database remains the authoritative source of document ownership and permissions.

---

# Temporary Preview Storage

Document previews use temporary storage:

```text
private_media/
└── generated_documents/
    └── temp/
```

Used for:

- Template previews
- Draft rendering
- Form previews before document creation

Characteristics:

- Automatically regenerated
- Not permanent
- Periodically cleaned

Cleanup process:

```python
cleanup_temp_previews()
```

removes files older than a configured threshold.

---

# Upload Limits

Configured globally:

```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600
```

Equivalent to:

```text
100 MB
```

This supports:

- Large PDF uploads
- Document assets
- High-resolution images

while still preventing unbounded memory usage.

---

# Backup Strategy

## Important Design Decision

Media files are intentionally **excluded from system backups**.

The encrypted backup system only stores:

- PostgreSQL database contents

It does **not** store:

- Public media files
- Private media files
- Generated PDFs
- Profile pictures
- Template assets

---

## Rationale

### Generated Documents

Generated contracts can be recreated because:

- Templates are stored in the database
- Document context data is stored in the database
- Signature attestations are stored in the database
- Signer assignments are stored in the database

If required, PDFs can be regenerated from stored metadata.

---

### Profile Pictures

Profile pictures and other user-uploaded media are considered non-critical.

Losing these files is acceptable compared to:

- Larger backup sizes
- Slower backup operations
- Increased storage costs

---

### Backup Goals

The backup system is designed primarily for:

- Disaster recovery
- Database restoration
- Recovery of business data
- Recovery of application state

rather than full file archival.

---

# Security Considerations

## Public vs Private Separation

Sensitive documents never reside in publicly served directories.

```text
media/           -> public
private_media/   -> protected
```

This reduces the risk of:

- URL guessing
- Direct file access
- Unauthorized downloads

---

## Permission Enforcement

Private files are only accessible through:

```python
FileResponse(...)
```

after permission validation.

Document ownership checks ensure users only access documents they are authorized to view.

---

## No Direct URLs

Private storage uses:

```python
base_url=None
```

meaning Django never generates public links to sensitive files.

All access must go through application logic.

---

# Storage Directory Layout

Example deployment structure:

```text
project/

├── static/
├── staticfiles/

├── media/
│   ├── profile_pictures/
│   └── uploads/

├── private_media/
│   └── generated_documents/
│       ├── contracts/
│       ├── temp/
│       └── previews/

└── backups/
```

---

# Summary

The AstroLink storage architecture separates files into public and private domains:

- **Static files** support the application UI.
- **Media files** store general user uploads.
- **Private media** stores contracts and sensitive PDFs.
- **Templates and assets** support dynamic document generation.
- **Generated documents are protected by application permissions rather than public URLs.**
- **Media is intentionally excluded from backups**, relying on database-backed regeneration of contracts and acceptance of limited media loss in exchange for simpler, faster backups.

This design prioritizes:

- Security
- Simplicity
- Recoverability of business-critical data
- Reduced backup size and operational overhead