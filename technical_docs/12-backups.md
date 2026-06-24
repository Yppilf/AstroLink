# Backup & Restore System

## Overview

The Backup & Restore subsystem provides administrators with a secure mechanism for exporting and restoring complete platform snapshots.

The system creates encrypted PostgreSQL database backups that can be downloaded and stored offline. These backups can later be restored to recover the entire application state, including users, projects, applications, documents, permissions, and all other platform data.

The primary objectives of this subsystem are:

* Disaster recovery
* Migration between environments
* Administrative archival
* Protection against accidental data loss

Backups are encrypted before leaving the server, ensuring that exported files cannot be read without the platform's encryption key.

---

## Architecture

The backup functionality consists of three components:

### Backup Export

Creates a PostgreSQL database dump and encrypts it before download.

### Backup Import

Accepts an encrypted backup file, decrypts it, and restores the database.

### Administrative Interface

Provides a web interface for authorized users to initiate exports and imports.

---

## Access Control

Backup operations are restricted to highly privileged users.

The following permissions are required:

* `create_supervisor`
* `create_student`
* `create_association`

These permissions effectively limit backup functionality to system-level administrative users.

All backup views are protected using:

```python
@external_user_permissions_required(
    "create_supervisor",
    "create_student",
    "create_association",
)
```

Unauthenticated users and regular platform users cannot access backup functionality.

---

# Backup Export Process

## Purpose

The export process generates a complete encrypted snapshot of the PostgreSQL database.

## Workflow

### Step 1: Create Temporary Dump File

A temporary PostgreSQL dump file is created:

```python
tempfile.NamedTemporaryFile(
    suffix=".dump",
    delete=False,
)
```

---

### Step 2: Execute PostgreSQL Dump

The system invokes:

```bash
pg_dump -Fc
```

using the configured database connection settings.

Example:

```bash
pg_dump \
    -Fc \
    -h HOST \
    -p PORT \
    -U USER \
    -d DATABASE
```

The dump is stored in PostgreSQL's custom binary format.

Advantages:

* Compact storage
* Faster restoration
* Preserves schema and data
* Supports transactional restores

---

### Step 3: Encrypt Backup

The generated dump is encrypted using:

```python
encrypt_file(
    dump_file,
    encrypted_file,
    settings.BACKUP_ENCRYPTION_KEY,
)
```

The encryption key is configured in:

```python
settings.BACKUP_ENCRYPTION_KEY
```

The plaintext database dump is deleted immediately after encryption.

---

### Step 4: Download Backup

The encrypted file is streamed to the user as:

```text
astrolink_YYYYMMDD_HHMMSS.backup.enc
```

using:

```python
FileResponse(...)
```

No unencrypted backup leaves the server.

---

# Backup Restore Process

## Purpose

Restore a previously exported encrypted backup.

## Warning

Restoration is destructive.

All current database contents are replaced with the contents of the backup.

Before restoration, administrators should ensure:

* The backup file is correct
* The backup is recent enough
* No users are actively using the system

---

## Workflow

### Step 1: Upload Backup

The administrator uploads a file through the restore interface.

Accepted file type:

```text
*.backup.enc
```

---

### Step 2: Explicit Confirmation

To prevent accidental restores, the administrator must check:

```text
I understand this will DELETE ALL DATA and restore from backup
```

Without confirmation the request is rejected.

---

### Step 3: Decrypt Backup

The uploaded encrypted file is decrypted using:

```python
decrypt_file(...)
```

and the configured:

```python
BACKUP_ENCRYPTION_KEY
```

If decryption fails:

* Restore is aborted
* Temporary files are deleted
* The request returns an error

This protects against:

* Corrupted backups
* Invalid files
* Incorrect encryption keys

---

### Step 4: Close Active Database Connections

Before restoration:

```python
connection.close()
```

is executed to ensure PostgreSQL can safely restore the database.

---

### Step 5: Restore Database

The system invokes:

```bash
pg_restore
```

with:

```bash
--clean
--if-exists
--no-owner
--no-privileges
```

Example:

```bash
pg_restore \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges
```

Meaning:

| Option            | Purpose                                |
| ----------------- | -------------------------------------- |
| `--clean`         | Drop existing objects before restoring |
| `--if-exists`     | Ignore missing objects                 |
| `--no-owner`      | Do not restore ownership metadata      |
| `--no-privileges` | Do not restore privilege assignments   |

This ensures restoration succeeds across environments and database instances.

---

### Step 6: Cleanup

Temporary files are deleted:

```python
os.remove(...)
```

for both:

* Encrypted upload
* Decrypted dump

No backup artifacts remain on disk after completion.

---

# Administrative Interface

## Backup Page

The administrative interface provides two actions:

### Download Encrypted Backup

Creates and downloads a fresh encrypted snapshot.

```text
Download Encrypted Backup
```

---

### Restore Backup

Allows administrators to upload an encrypted backup file.

Requirements:

* Backup file selected
* Confirmation checkbox checked

The interface prominently warns users that restoration is destructive.

---

# Security Model

## Encryption at Rest

Exported backups are never distributed in plaintext.

The workflow is:

```text
Database
    ↓
PostgreSQL Dump
    ↓
Encryption
    ↓
Encrypted Backup File
```

Only encrypted files leave the server.

---

## Controlled Access

Backup operations require elevated permissions.

Regular users cannot:

* Export data
* Download backups
* Restore backups

---

## Temporary File Handling

The system uses temporary files for:

* PostgreSQL dumps
* Uploaded backups
* Decrypted restore files

Files are removed immediately after use.

---

## Restore Confirmation

Restoration requires explicit user acknowledgement.

This prevents accidental database replacement through misclicks or form submission mistakes.

---

# Dependencies

The subsystem depends on:

### PostgreSQL Utilities

Required on the host machine:

```text
pg_dump
pg_restore
```

These utilities must be available on the system path.

---

### Encryption Utilities

Provided by:

```python
astrolink.encryption_utils
```

Functions:

```python
encrypt_file(...)
decrypt_file(...)
```

These implement backup encryption and decryption.

---

# Operational Considerations

## Recommended Backup Strategy

Production deployments should:

* Export backups regularly
* Store backups offsite
* Verify restoration procedures periodically
* Protect encryption keys separately from backups

---

## Key Management

The backup encryption key is critical.

Loss of:

```python
BACKUP_ENCRYPTION_KEY
```

means encrypted backups become unrecoverable.

Administrators should maintain secure key management procedures.

---

## Disaster Recovery

A complete system recovery requires:

1. Application source code
2. Environment configuration
3. Backup encryption key
4. Latest encrypted backup

Together these components allow full restoration of platform functionality and data.

---

# Design Rationale

The backup subsystem was designed around several principles:

### Simplicity

Relies on PostgreSQL's native backup tooling instead of custom serialization logic.

### Security

All exported backups are encrypted before distribution.

### Reliability

Uses PostgreSQL's proven dump and restore mechanisms.

### Portability

Backups can be restored on different environments without ownership or privilege conflicts.

### Administrative Safety

Destructive actions require explicit confirmation and are restricted to privileged users.

This provides a secure and maintainable disaster recovery mechanism for the platform.
