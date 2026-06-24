# Documentation App

## Purpose

The `documentation` app provides integrated user documentation for AstroLink. It allows platform users to access role-specific guides and usage instructions directly within the application.

Unlike technical documentation intended for developers, this app serves end users such as students, supervisors, programme coordinators, and associations.

Documentation pages are written in Markdown and rendered dynamically through Django views. This allows documentation content to be updated without modifying templates or application logic.

---

# Architecture Overview

The application consists of three main components:

1. Markdown documentation files
2. Navigation configuration
3. Markdown rendering views

---

## Documentation Pages

```
/documentation/<slug>/
```

Examples:

```
/documentation/students/
/documentation/supervisors/
/documentation/projects/
```

The slug determines which Markdown file is loaded.

---

# Markdown Page Loading

Documentation pages are served through the `docs_page()` view.

Example:

```python
def docs_page(request, slug):
    file_path = BASE_DIR / "docs" / f"{slug}.md"
```

The view:

1. Receives the requested slug.
2. Locates the corresponding Markdown file.
3. Reads the file contents.
4. Converts Markdown into HTML.
5. Generates a table of contents.
6. Renders the documentation template.

If the file does not exist, a 404 page is displayed.

---

# Navigation System

The documentation sidebar is generated from a static configuration:

```python
DOCS_NAV = [
    {"slug": "supervisors", "title": "Supervisors"},
    {"slug": "associations", "title": "Associations"},
    {"slug": "students", "title": "Students"},
    {"slug": "coordinators", "title": "Coordinators"},
    {"slug": "projects", "title": "Projects & Case Studies"},
    {"slug": "applications", "title": "Applications"},
    {"slug": "researchgroups", "title": "Research Groups"},
    {"slug": "tags", "title": "Tags"},
    {"slug": "documents", "title": "Documents"},
]
```

Each navigation item corresponds directly to a Markdown document.

Example:

```python
{
    "slug": "students",
    "title": "Students"
}
```

expects the file:

```
docs/students.md
```

---

# Automatic Table of Contents

A table of contents is automatically generated from Markdown headings.

Example:

```markdown
# Students

## Creating an Account

## Applying for a Project

## Managing Documents
```

Produces a nested navigation structure in the sidebar.

The table of contents updates automatically whenever headings are added or removed.

No manual maintenance is required.

---

# User Interface

Documentation pages are rendered inside the standard AstroLink layout.

Features include:

* Consistent application styling
* Responsive layout
* Sidebar navigation
* Automatic table of contents
* Markdown-based content management
* Direct integration with platform authentication

The active documentation page is highlighted within the navigation menu.

---

# Updating Documentation

Documentation updates require only editing Markdown files.

Example:

```
docs/students.md
```

No database migrations are required.

No code changes are required.

No application restart is required.

Changes become visible immediately after deployment.

---

# Adding New Documentation Pages

To create a new page:

### 1. Create a Markdown file

Example:

```
docs/notifications.md
```

### 2. Add a navigation entry

```python
{
    "slug": "notifications",
    "title": "Notifications"
}
```

### 3. Deploy changes

The new page automatically becomes available at:

```
/documentation/notifications/
```

---

# Design Rationale

The documentation system was intentionally designed as a file-based solution rather than a database-backed content management system.

Advantages include:

* Version controlled documentation
* Documentation changes reviewed through Git
* Simple deployment process
* No additional database tables
* No administrative interface required
* Easy contribution by developers
* Automatic rollback through source control

This approach keeps user documentation synchronized with application releases and reduces long-term maintenance complexity.

---

# Dependencies

The documentation app depends on:

* Django URL routing
* Django template rendering
* Markdown rendering utilities
* Base AstroLink templates

No database models are defined by this application.

No migrations are required.
