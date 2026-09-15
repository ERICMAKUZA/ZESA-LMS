# User Management and Notification Delivery Design

## Goal

Give Admin and Superadmin users safe in-portal account administration, then deliver consistent, auditable email and in-system notifications for admissions, training schedules, assessments, payment, and certificates.

## Scope and Roles

- `ADMIN` and `SUPERADMIN` may create users, assign lecturer status, deactivate users, and reactivate users.
- `LECTURER` may not administer accounts. They retain existing course/training-operation access.
- `STUDENT`, `LECTURER`, and other active users receive email and bell notifications. SMS and WhatsApp remain unused.
- Moodle remains the learning engine. This design extends the portal operations layer only.

## User Management

The Users page gains an Admin/Superadmin-only Create User flow with first name, last name, email, temporary password, department, and phone. The server validates and hashes the password through the existing account creation path; no plaintext password is persisted or displayed after creation. The account starts as `STUDENT` unless the administrator explicitly assigns it as lecturer afterwards.

Each active non-lecturer row exposes **Assign as Lecturer**. This changes the account role to `LECTURER` without changing its identity, history, applications, or notifications. Each active user exposes **Deactivate**; each inactive user exposes **Reactivate**. Deactivation sets `is_active=False`, blocks future sign-in, preserves all audit records and course assignments, and removes a lecturer from the existing active-lecturer course picker automatically. Existing sessions are rejected by authenticated API access when the account is inactive.

## Notification Architecture

The existing `Notification` record remains the canonical delivery/audit object. Every event creates one notification per recipient and delivers it through both channels:

1. An in-system bell item with unread/read state and action link.
2. An email sent through the existing notification worker/service.

Messages are code-owned templates, not portal-editable content. The supplied wording, Stanbic banking details, and collection hours are versioned in the application and covered by tests. Each notification stores its rendered message, recipient, application/event link, delivery state, error state, and timestamp, so later template changes do not alter historic communications.

## Notification Events

### Acceptance and Payment

Approval sends the student:

> You have been accepted for {course_name}, commencing on {commencement_date}. You are required to pay full course fees of USD {amount} by {payment_due_date}. Banking details: Bank: STANBIC, Park Lane Branch. Account Name: ZESA National Training Centre. Account Number: 9140000940908 (Nostro). Upload proof of payment.

`payment_due_date` is an explicit intake field, defaulting to the course commencement date when not set. The notification links to the student application/payment path.

### Commencement and Attendance

Publishing a commencement event sends enrolled students:

> The {course_name} course will commence on {date}. Kindly confirm attendance.

The bell action has **Confirm attendance** and **Defer**. Confirmation records the response. Deferral moves the enrolment to the next open intake of the same course when a place is available, updating capacity atomically and notifying the student. If no intake is available, the defer request remains pending for staff review and the student receives a clear in-system outcome.

### Deferral and Certificate Collection

An authorised training user can publish a course deferral event:

> Please be advised {course_name} course which was scheduled to commence on {original_date} has been postponed to {new_date_or_tba}.

Certificate issue sends:

> Your certificates for {course_name} are ready for collection. Collection time 0830-1600hrs Monday to Friday.

### Calendar and Assessment Events

An `AcademicCalendarEvent` records a type, title, start/end dates, audience, optional course or intake, optional timetable/material link, and publisher. Supported types are `EXAMINATION`, `SEMESTER_START`, `SEMESTER_END`, `BLOCK_START`, `BLOCK_END`, `SEMESTER_BREAK`, `EXAM_FEE`, and `MARKS_DEADLINE`.

Publishing events sends the required audience-specific templates:

- Examination dates include `{start_date}`, `{end_date}`, and a timetable link/attachment.
- Semester/block start and end includes the run dates and fee-settlement reminder.
- Semester break includes start/end dates.
- Final marks sends students “Kindly verify your coursework marks by {date}” and lecturers “Deadline for submission of marks: {date}.”
- Examination fees tells students to verify the total amount with the current examination-fee schedule.

### Quarterly Upcoming Courses

A Celery Beat job runs one month before each quarter: 1 December, 1 March, 1 June, and 1 September. It broadcasts the next three months of active courses whose type code is `HEXCO` or `UZ`. The rendered notification lists the relevant course names, upcoming intake dates, and action links. The job is idempotent per quarter and recipient.

## Data and API Boundaries

- User administration is exposed by protected Admin/Superadmin endpoints: create, assign lecturer, deactivate, and reactivate.
- `User.is_active` is authoritative for login and lecturer availability.
- `CourseSchedule` gains `payment_due_date`.
- `EnrollmentAttendanceResponse` stores enrolment, response (`CONFIRMED`, `DEFERRED`, `PENDING_STAFF`), response date, target intake, and audit note.
- `AcademicCalendarEvent` stores published schedule-driven notifications and never changes the stored notification content.
- Dedicated service functions render and queue each event; workflow/payment/enrolment/certificate code calls those functions instead of embedding message strings.

## Validation and Safety

- Email is unique; passwords use the existing Django validation and hashing rules.
- Only Admin/Superadmin may change account status or lecturer role.
- Inactive users cannot obtain or use authenticated API access.
- Deactivation does not delete the user or remove historical lecturer assignments.
- Deferral never overfills an intake; capacity updates use a transaction and row lock.
- Events require meaningful dates for their type; examination events require a timetable link or attachment.
- Quarterly broadcasts use a deterministic quarter key to prevent duplicate sends.

## Testing Strategy

- Backend tests cover account create/password login, permissions, lecturer assignment, deactivation/reactivation, and inactive lecturer exclusion.
- Notification tests assert the exact required content, recipient audience, bell record, email dispatch, delivery failure audit, and idempotency.
- Attendance/defer tests cover confirmation, successful next-intake move, full/no-intake pending behaviour, and capacity safety.
- Calendar tests cover each event template, timetable action link, audience selection, and quarterly `HEXCO`/`UZ` broadcasts.
- End-to-end tests cover user creation/login, approval/payment notification, attendance confirmation/deferment, certificate collection, and bell/email delivery without changing Moodle enrolment behaviour.
