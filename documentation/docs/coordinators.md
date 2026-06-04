# Programme Coordinators

Programme Coordinators are responsible for monitoring thesis-related activities within a specific academic scope. Unlike [breadcrumb-inline:supervisors|/documentation/supervisors/ ::] and [breadcrumb-inline:associations|/documentation/associations/ ::], coordinators do not create [breadcrumb-inline:projects or case studies|/documentation/projects/ ::] themselves. Instead, they are granted visibility into students, applications and related activity based on their assigned programme and academic level.

Programme Coordinator accounts can only be created by administrators and cannot be self-registered.

## Coordinator Profile

In addition to the standard user profile fields, coordinators have two additional fields:

- Programme
- Level

These fields determine which students and thesis applications are visible to the coordinator.

A coordinator cannot edit their own programme or level. These values are managed by system administrators.

## Coordinator Scope

A coordinator's visibility is automatically restricted to students whose:

- Study programme matches the coordinator's programme
- Academic level matches the coordinator's level

Students outside this scope are not visible to the coordinator outside of the direct URL access to their public profile.

This visibility restriction is enforced throughout the application, including student overviews, application overviews and timeline views.

## Coordinator Management

Users with the appropriate permissions can access the coordinator overview.

The overview contains:

- Name
- Email Address
- Programme
- Level

Administrators may update coordinator configuration directly from this overview. Coordinators themselves cannot modify their assigned scope.

## Student Overview

Programme Coordinators have access to a filtered student overview containing only students within their assigned scope.
The overview includes:

- Student Name
- Email Address
- Student Number
- Total Thesis Applications
- Pending Applications
- Confirmed Applications

These statistics only include applications related to thesis opportunities, which are defined as projects and case studies with the [breadcrumb-inline:thesis tag|/documentation/tags/ ::].

## Student Profiles

When viewing a student profile, coordinators can access an additional Applications tab.

This tab contains all thesis-related applications submitted by the student that fall within the coordinator's scope. Applications outside the coordinator's assigned programme and level are never shown. Coordinators have visibility into the application process but cannot submit applications on behalf of students.

## Supervisor Profiles

Programme Coordinators can also view supervisor profiles.

When viewing a supervisor profile, the Applications tab contains thesis applications submitted by students within the coordinator's assigned scope to projects owned by that supervisor.

This allows coordinators to monitor supervision activity without granting unrestricted access to all student data.

## Application Timeline

Programme Coordinators have access to a dedicated timeline dashboard for monitoring thesis activity.
The timeline aggregates events from thesis applications within the coordinator's scope, and allows filtering based on student, supervisor and project/case study.
Available filter options are automatically restricted to data the coordinator is allowed to access.

### Timeline Events

The timeline records significant events in the lifecycle of an application, including:

- Application Submitted
- Application Accepted
- Application Rejected
- Application Confirmed

Where applicable, [breadcrumb-inline:document-related events|/documentation/documents/ ::] are also shown:

- Document Created
- Document Edited
- Document Locked

Events are displayed chronologically, allowing coordinators to monitor progress across multiple thesis trajectories.

## Permissions

Programme Coordinators primarily have read-only access.

Depending on the permissions assigned to their role, they may be able to:

- View students within their scope
- View coordinator profiles
- View thesis applications within their scope
- Access the thesis activity timeline

Programme Coordinators do not:

- Create students
- Create supervisors
- Create associations
- Create projects
- Create case studies
- Modify student programme assignments
- Modify their own visibility scope

Their role is intended for monitoring, oversight and academic coordination rather than operational management.