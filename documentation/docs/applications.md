# Applications

Applications are the central mechanism through which students interact with projects, case studies, and general opportunities within the platform. They represent a structured request from a student to participate in an opportunity and form the basis of the selection and approval workflow used by supervisors and associations.

An application always belongs to a single student and may optionally be linked to:

- A **Project** (hosted by a supervisor)
- A **Case Study** (managed by an association on behalf of a company)
- A **General Application** (not linked to a specific project or case study, but routed to an association)

---

## Creating an Application

Applications are created by students through the platform interface. When submitting an application, a student provides:

- Experience — Relevant background or skills
- Motivation — Why they are interested in the opportunity
- Interest — Their specific interest in the project or case study
- Optional comments — Additional remarks

Depending on the application type, the student selects either a project, a case study, or neither (for general applications).

Upon submission:

- The application is stored with status **PENDING**
- The associated supervisor or association is notified via email (for project-based applications)
- The application becomes visible according to the visibility rules described below

---

## Application Types

### Project Applications

- Linked to a specific project
- Managed by a **Supervisor**
- Used primarily for academic or research-based work

### Case Study Applications

- Linked to a company case study
- Managed by an **Association**
- Represent collaboration with external companies

### General Applications

- Not linked to a specific project or case study
- Routed to a selected association
- Used for open-ended interest or exploration

---

## Application Status Pipeline

Applications follow a structured lifecycle:

- **PENDING** — The application is awaiting review
- **ACCEPTED** — The application has been accepted by a supervisor or association
- **REJECTED** — The application has been rejected
- **CONFIRMED** — The student has confirmed acceptance

### Confirmation Requirement

Once an application has been marked as **ACCEPTED**, the student must confirm the application within a certain number of days specified upon acceptance, with the default being **14 days**. If the deadline is exceeded, the application can no longer be confirmed.

---

## Visibility and Permissions

Application visibility and editing rights depend on the application type and the user’s role.

| Applied to | Visible to | Updatable by |
|------------|------------|--------------|
| Project | Student, Project Supervisor, Programme Coordinator (if within scope and thesis-related) | Supervisor |
| Case Study | Student, Association managing the company, Programme Coordinator (if within scope and thesis-related) | Association |
| General Application | Student, Selected Association | Selected Association |

---

### Coordinator Restrictions

Programme coordinators can only access applications when:

- The student belongs to their assigned programme and level
- The application is marked as relevant (e.g. thesis-related via tags)
- The application falls within their scoped oversight

This ensures coordinators only access applications relevant to their academic responsibility.

---

## Review Process

Once submitted, applications are reviewed by the responsible party:

### Supervisors and Associations can:

- Review applications
- Accept or reject applications
- Provide a mandatory comment when making a decision
- Assign confirmation deadline
- Toggle closing of oppurtunity upon confirmation
- Optionally trigger document creation during acceptance

### Acceptance

When an application is accepted:

- Status is set to **ACCEPTED**
- The acceptance timestamp is recorded
- Optional documents may be created for follow-up workflow steps
- The student is notified via email

### Rejection

When an application is rejected:

- Status is set to **REJECTED**
- The rejection timestamp is recorded
- The student is notified via email

---

## Student Confirmation

If an application is accepted, the student can:

- Review the decision and any supervisor comments
- Confirm the application within the allowed timeframe

Once confirmed:

- Status is set to **CONFIRMED**
- Confirmation timestamp is recorded
- The application is considered finalized
- If set, the project/case study will no longer allow applications

---

## Ignoring Applications

Users may choose to ignore applications in their personal view. Ignored applications:

- Are hidden from the user’s application overview
- Do not affect the underlying application record
- Can be restored only through system-level mechanisms (not user-facing)

---

## Related Documents

During the acceptance process, supervisors or associations may optionally generate documents linked to the application. These documents:

- Are associated with the application
- May require student input or completion
- Are tracked alongside the application lifecycle

Document handling and workflows are described in the dedicated document management section.

---

## Notifications

The system automatically sends notifications during key events:

- Application submission (project applications)
- Application acceptance or rejection
- Supervisor notifications for new submissions
- Optional academic supervisor notifications (for PhD-related supervision structures)

These notifications ensure timely communication between students and reviewers.

---