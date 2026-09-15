# User Management and Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe Admin/Superadmin user lifecycle controls and code-owned email/bell notifications for the full training lifecycle.

**Architecture:** Extend `accounts` for protected user lifecycle actions and enforce inactive-user rejection at authentication. Keep `workflows.Notification` as the canonical rendered-message audit record; add focused template, attendance-response, and academic-calendar services rather than scattering message strings across viewsets. Moodle remains unchanged except for existing enrolment links.

**Tech Stack:** Django, Django REST Framework, Simple JWT, Celery/Beat, PostgreSQL, React/Next.js/TypeScript.

**Spec:** `/Users/dazzmurenga/Documents/ZESA-LMS/docs/superpowers/specs/2026-09-01-user-management-and-notifications-design.md`

## Global Constraints

- Only `ADMIN` and `SUPERADMIN` may create accounts, assign lecturer status, deactivate, or reactivate users.
- Passwords use Django validation and hashing; plaintext is never persisted or returned.
- Notifications deliver email and in-system bell records only; SMS and WhatsApp are not used.
- Required message wording and Stanbic details are code-owned templates, not editable portal content.
- `is_active=False` blocks sign-in and authenticated API use while preserving history and course assignments.
- Lecturer availability remains `role=LECTURER` and `is_active=True`.
- Deferral capacity updates are transactional and may not overfill an intake.
- UAT deploy remains a reviewed PR to protected `uat`.

---

## File Structure

- `backend/apps/accounts/serializers.py`, `views.py`, `urls.py`, `permissions.py`, `tests.py` - protected account lifecycle API and inactive access protection.
- `frontend/src/app/admin/users/page.tsx`, `frontend/src/lib/api.ts`, `frontend/src/types/index.ts` - create user and lecturer/status controls.
- `backend/apps/workflows/templates.py` - exact code-owned rendered messages and banking constants.
- `backend/apps/workflows/services.py`, `tasks.py`, `tests.py` - one audit record and dual-channel dispatch per event.
- `backend/apps/courses/models.py`, `migrations/0009_schedule_payment_due_date_and_calendar_events.py`, `serializers.py`, `views.py`, `urls.py`, `tests.py` - payment due dates and academic calendar events.
- `backend/apps/enrollments/models.py`, `migrations/0005_attendance_response.py`, `views.py`, `urls.py`, `tests.py` - attendance confirmation/deferment response and safe intake transfer.
- `frontend/src/app/dashboard/learning/page.tsx`, `frontend/src/app/admin/training/page.tsx` - student response actions and staff calendar publishing.

### Task 1: Add Protected User Lifecycle Controls

**Files:** Modify `backend/apps/accounts/{serializers.py,views.py,urls.py,permissions.py,tests.py}`; modify `frontend/src/app/admin/users/page.tsx`; modify `frontend/src/{lib/api.ts,types/index.ts}`.

**Interfaces:** Produces `POST /api/admin/users/`, `POST /api/admin/users/{id}/assign-lecturer/`, `POST /api/admin/users/{id}/deactivate/`, and `POST /api/admin/users/{id}/reactivate/`.

- [ ] **Step 1: Write failing API tests**

```python
def test_admin_creates_a_login_user_and_assigns_lecturer(self):
    self.client.force_authenticate(self.admin)
    response = self.client.post("/api/admin/users/", {
        "email": "new.lecturer@zesa.co.zw", "first_name": "New", "last_name": "Lecturer",
        "password": "SafePass123!", "password_confirm": "SafePass123!",
    }, format="json")
    user = User.objects.get(email="new.lecturer@zesa.co.zw")
    self.assertTrue(user.check_password("SafePass123!"))
    self.assertEqual(self.client.post(f"/api/admin/users/{user.id}/assign-lecturer/").status_code, 200)

def test_deactivated_user_cannot_login_or_appear_as_available_lecturer(self):
    self.client.force_authenticate(self.admin)
    self.client.post(f"/api/admin/users/{self.lecturer.id}/deactivate/")
    self.assertFalse(User.objects.get(pk=self.lecturer.id).is_active)
    self.assertEqual(self.client.get("/api/admin/lecturers/").data, [])
```

- [ ] **Step 2: Run the failing tests**

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/user-notification-tests.sqlite REDIS_URL=redis://localhost:6379/0 CELERY_BROKER_URL=redis://localhost:6379/0 CELERY_RESULT_BACKEND=redis://localhost:6379/1 ../.venv/bin/python manage.py test apps.accounts.tests -v 2
```

- [ ] **Step 3: Implement the protected create/action viewset and UI**

Use `IsAdmin`; use `UserCreateSerializer` with the existing password hashing; expose no password in `UserSerializer`. Add an `IsActiveUser` authentication permission and attach it globally or to protected views so existing tokens fail once the account is inactive. Add a Users-page modal and mutation controls; render React Query invalidation after each successful action.

- [ ] **Step 4: Run backend tests and frontend build**

```bash
../.venv/bin/python manage.py test apps.accounts apps.courses.tests -v 2
cd ../../frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts frontend/src/app/admin/users/page.tsx frontend/src/lib/api.ts frontend/src/types/index.ts
git commit -m "feat: manage user and lecturer access"
```

### Task 2: Create Code-Owned Notification Templates and Acceptance Delivery

**Files:** Create `backend/apps/workflows/templates.py`; modify `services.py`, `tasks.py`, `tests.py`; modify `backend/apps/applications/views.py`; modify `backend/apps/courses/models.py` and migration.

**Interfaces:** Produces `queue_acceptance_notification(application)`, `queue_certificate_collection_notification(certificate)`, and `CourseSchedule.payment_due_date`.

- [ ] **Step 1: Write failing template and approval tests**

```python
def test_approval_queues_exact_acceptance_email_and_bell_record(self):
    application = ApplicationFactory(status=ApplicationStatus.UNDER_REVIEW)
    application.approve()
    notification = Notification.objects.get(application=application)
    self.assertIn("STANBIC, Park Lane Branch", notification.message)
    self.assertIn("9140000940908", notification.message)
    self.assertIn(application.course.fullname, notification.subject)
```

- [ ] **Step 2: Run the failing workflow test**

```bash
../.venv/bin/python manage.py test apps.workflows.tests -v 2
```

- [ ] **Step 3: Implement renderer/service integration**

Define constants for bank, account name, account number, and collection hours. Render dates from intake, defaulting `payment_due_date` to intake start. Queue one `Notification` whose worker sends email and whose record drives the bell; call the acceptance function from the existing approval success path and certificate function from certificate issue.

- [ ] **Step 4: Run tests and migration check**

```bash
../.venv/bin/python manage.py test apps.workflows apps.applications.tests -v 2
../.venv/bin/python manage.py makemigrations --check
```

- [ ] **Step 5: Commit**

```bash
git add backend/apps/workflows backend/apps/applications backend/apps/courses
git commit -m "feat: send training lifecycle notifications"
```

### Task 3: Add Attendance Confirmation and Safe Deferral

**Files:** Modify `backend/apps/enrollments/{models.py,views.py,urls.py,tests.py}`; create migration `0005_attendance_response.py`; modify `backend/apps/workflows/{templates.py,services.py,tests.py}`; modify student learning page.

**Interfaces:** Produces `POST /api/enrollments/{id}/attendance-response/` with `{response: "CONFIRMED"|"DEFER"}` and `EnrollmentAttendanceResponse`.

- [ ] **Step 1: Write failing response/deferment tests**

```python
def test_defer_moves_enrollment_to_next_open_intake_without_overfilling(self):
    response = self.client.post(f"/api/enrollments/{self.enrollment.id}/attendance-response/", {"response": "DEFER"})
    self.assertEqual(response.status_code, 200)
    self.enrollment.refresh_from_db()
    self.assertEqual(self.enrollment.schedule, self.next_schedule)
    self.assertEqual(self.next_schedule.enrolled_count, 1)
```

- [ ] **Step 2: Run the failing enrolment test**

```bash
../.venv/bin/python manage.py test apps.enrollments.tests -v 2
```

- [ ] **Step 3: Implement transaction-safe response service and UI**

Lock the current and next matching open schedule with `select_for_update`; update both counters and enrollment schedule in one transaction. Save `PENDING_STAFF` with no target when no capacity/intake exists. Add Confirm attendance/Defer buttons to the student learning card and send the resultant notification.

- [ ] **Step 4: Verify tests**

```bash
../.venv/bin/python manage.py test apps.enrollments apps.workflows.tests -v 2
cd ../../frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add backend/apps/enrollments backend/apps/workflows frontend/src/app/dashboard/learning/page.tsx
git commit -m "feat: confirm attendance and defer enrolments"
```

### Task 4: Add Calendar Events and Quarterly Broadcasts

**Files:** Modify `backend/apps/courses/{models.py,serializers.py,views.py,urls.py,tests.py}`; migration `0009_schedule_payment_due_date_and_calendar_events.py`; modify workflow services/tasks/tests and Celery Beat configuration; modify `frontend/src/app/admin/training/page.tsx`.

**Interfaces:** Produces `AcademicCalendarEvent`, protected publish endpoint, and idempotent `broadcast_upcoming_courses(quarter_key)` task.

- [ ] **Step 1: Write failing calendar/broadcast tests**

```python
def test_exam_event_requires_timetable_and_notifies_enrolled_students(self):
    response = self.client.post("/api/courses/calendar-events/", {
        "event_type": "EXAMINATION", "course": self.course.id,
        "start_date": "2026-11-02", "end_date": "2026-11-06", "timetable_url": "",
    }, format="json")
    self.assertEqual(response.status_code, 400)

def test_quarterly_broadcast_is_idempotent_per_recipient(self):
    broadcast_upcoming_courses("2026-Q4")
    broadcast_upcoming_courses("2026-Q4")
    self.assertEqual(Notification.objects.filter(subject__startswith="Upcoming courses ALERT").count(), 1)
```

- [ ] **Step 2: Run failing calendar tests**

```bash
../.venv/bin/python manage.py test apps.courses.tests apps.workflows.tests -v 2
```

- [ ] **Step 3: Implement event model, renderers, publishing form, and Beat task**

Validate event-specific dates and examination timetable link; map each event type to the approved code-owned wording and correct audience. Schedule quarterly task dates on Dec 1, Mar 1, Jun 1, and Sep 1; select active `HEXCO`/`UZ` courses/intakes in the following three months; save a quarter/recipient event key before queueing.

- [ ] **Step 4: Verify backend and frontend**

```bash
../.venv/bin/python manage.py test apps.courses apps.workflows apps.enrollments -v 2
cd ../../frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add backend/apps/courses backend/apps/workflows frontend/src/app/admin/training/page.tsx
git commit -m "feat: publish academic calendar notifications"
```

### Task 5: Final Regression and Protected UAT Release

**Files:** Verify all changed backend/frontend files and GitHub Actions/GitOps state.

- [ ] **Step 1: Run clean migration and regression suite**

```bash
rm -f /tmp/user-notification-tests.sqlite
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/user-notification-tests.sqlite REDIS_URL=redis://localhost:6379/0 CELERY_BROKER_URL=redis://localhost:6379/0 CELERY_RESULT_BACKEND=redis://localhost:6379/1 ../.venv/bin/python manage.py migrate --noinput
../.venv/bin/python manage.py test apps.accounts apps.courses apps.applications.tests apps.enrollments apps.workflows -v 2
../.venv/bin/python manage.py makemigrations --check
cd ../../frontend && npm run build
```

- [ ] **Step 2: Perform UAT acceptance checks**

```text
1. Admin creates a user, signs in with the supplied email/password, assigns lecturer, then deactivates and reactivates the user.
2. Reviewer approves an application and the student receives both acceptance email and unread bell item with fee/bank details.
3. Student confirms attendance; separately defer a student to a next open intake and verify capacity/audit/notification.
4. Publish each calendar event type and verify the correct recipient, text, dates, and timetable link.
5. Issue a certificate and verify collection notification; run the quarterly task twice and verify no duplicate recipient messages.
```

- [ ] **Step 3: Push branch and open/update PR**

```bash
git push origin HEAD:codex/user-management-notifications-uat
gh pr create --base uat --head codex/user-management-notifications-uat --title "feat: manage users and training notifications" --body "Adds protected user lifecycle controls, code-owned email/bell templates, attendance responses, calendar events, and quarterly broadcasts."
```

- [ ] **Step 4: Monitor approved UAT deployment**

Verify GitHub Actions success, GitOps image update, Argo `moodle-uat` sync/health, and web/worker/beat pod readiness before reporting deployment.

## Self-Review

**Spec coverage:** Task 1 covers account lifecycle and active access; Task 2 covers canonical notification delivery, approval/payment and certificate content; Task 3 covers commencement attendance/deferment/capacity; Task 4 covers all calendar events and quarterly broadcasts; Task 5 covers end-to-end acceptance and UAT release.

**Placeholder scan:** This plan has no `TODO`, `TBD`, or unspecified validation/test steps.

**Type consistency:** Task 2 produces notification services consumed by Tasks 3-4. Task 3 produces attendance-response state used only by student learning UI. Task 4 produces calendar events and the quarterly broadcast task. All use `Notification` as the single audit/delivery record.
