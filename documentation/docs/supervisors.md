# Supervisors

Supervisors are a special type of user within the application who are responsible for guiding, evaluating, and collaborating on student projects and academic activities. They represent academic or professional mentors and can be linked to students through [breadcrumb-inline:projects|/documentation/projects/ ::]. Supervisors have a standard user account, extended with additional profile information and functionality specific to supervision tasks.

---

## Supervisor Profile Data

In addition to the default user fields (such as name, email, and phone number), supervisors have access to the following profile information:

- Biography  
- Phone number (P-number / internal contact reference)  
- Profile picture  
- Academic supervisor (optional self-relation used for hierarchical PhD supervision structure)

If a supervisor is linked to another supervisor as an academic supervisor, they are considered a PhD student under that supervisor. This relationship is reflected in profile displays.

---

## How Supervisors Are Created

Supervisor accounts can be created in two ways:

### 1. Direct Registration (Admin Only)

Administrators can create supervisor accounts directly through the admin registration interface.

- A role of **Supervisor** is assigned during creation
- The user receives an email notification upon account creation
- The account is created in an active state by default or may require further approval depending on configuration

This method is primarily used for internal onboarding of supervisors.

---

### 2. Supervisor Signup Request (Pending Approval Flow)

Supervisors can also register themselves using the public signup form.

When a user signs up as a supervisor:

- A user account is created with the role **Supervisor**
- The account is marked as **inactive**
- The supervisor cannot log in yet
- The account is placed in a **pending approval list**

An administrator must approve the account before it becomes active.

Once approved:

- The account is activated
- The user receives a confirmation email
- The supervisor can log in and use the system

Pending supervisors can be managed via the supervisor approval interface in the admin tools.

---

## What Supervisors Can Do

Once approved and active, supervisors gain access to supervisor-specific functionality within the application.

### 1. Manage Their Profile

Supervisors can:

- Update their biography
- Upload or change their profile picture
- Maintain contact information (such as phone number)
- View their academic supervision relationships (if applicable)

---

### 2. Create and Manage References

Supervisors can create, update, and delete **references** associated with their profile.

A reference consists of:

- Title
- Description
- Optional link

References are publicly visible to authenticated users and are used to showcase expertise, experience, or external work.

Each reference is strictly owned by the supervisor who created it and cannot be edited by others.

---

### 3. Supervise Students (PhD / Academic Structure)

Supervisors can be assigned as academic supervisors to other supervisors (or PhD students).

This creates a hierarchical relationship:

- A supervisor may have multiple PhD students
- A supervisor may themselves be a PhD student under another supervisor

This relationship is visible in their profile display and is used for academic structuring within the system, but does not affect functionality within AstroLink.

---

### 4. View and Interact with [breadcrumb-inline:Applications|/documentation/applications/ ::]

Supervisors can view applications made for their projects.

- View applications submitted by students to their projects
- Review application details including motivation and experience
- Track and update application status updates

Supervisors can only modify applications in contexts where they are explicitly the responsible party (e.g. when a project is owned by them). Academic supervisors do get notified when their PhD student receives an application, but they do not directly manage this application.

---

## Summary

Supervisors are core academic participants in the system. They:

- Support students through supervision
- Maintain a professional profile with references and academic information
- Participate in application workflows related to their projects
- Can exist in hierarchical academic structures (PhD supervision chains)

They are either created directly by administrators or through a controlled approval-based signup process.