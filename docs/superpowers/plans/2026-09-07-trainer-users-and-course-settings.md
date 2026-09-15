# Trainer Users and Course Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let administrators create Trainer and Lecturer accounts, make active lecturers assignable to courses, and manage course types and their certification options from the portal.

**Architecture:** Extend the existing custom `User.Role` choices with a first-class `TRAINER` role and accept only `TRAINER` or `LECTURER` in the administrator's create-user endpoint. Reuse the existing `CourseType` and `CertificationType` models and APIs, expose them through a Settings page, and change course creation to select a configurable course type and only that type's certification options.

**Tech Stack:** Django 5, Django REST Framework, PostgreSQL-compatible Django migrations, Next.js, TypeScript, TanStack Query, Tailwind CSS.

**Spec:** `/Users/dazzmurenga/Documents/ZESA-LMS/docs/superpowers/specs/2026-09-01-training-qualification-management-design.md`

## Global Constraints

- Do not modify `master`; build on the stacked `codex/user-management-notifications` branch.
- The create-user role selector shows only `Trainer` and `Lecturer` until RBAC replaces this temporary role model.
- A deactivated lecturer must never appear in the course lecturer picker.
- A course may have multiple lecturers and must retain at least one assigned lecturer.
- Course types and certification types are configured in the portal; a certification option must belong to the selected course type.
- Keep the legacy generic `Course.level` database field for backwards compatibility, but do not present it as the configurable course classification field.

---

### Task 1: Add the trainer role and secure user creation

**Files:**
- Modify: `backend/apps/accounts/models.py`
- Create: `backend/apps/accounts/migrations/0006_add_trainer_role.py`
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/permissions.py`
- Modify: `backend/apps/accounts/tests.py`

**Interfaces:**
- Consumes: `POST /api/admin/users/` with `role` in `{TRAINER, LECTURER}`.
- Produces: persisted `User.Role.TRAINER`; `CanManageTraining` grants course-management access to trainers; invalid roles return a field validation error.

- [ ] **Step 1: Write the failing API tests**

```python
def test_admin_creates_trainer_and_lecturer_accounts(self):
    self.client.force_authenticate(self.admin)
    for role in (User.Role.TRAINER, User.Role.LECTURER):
        response = self.client.post("/api/admin/users/", {
            "email": f"{role.lower()}@example.com", "first_name": role.title(),
            "last_name": "User", "role": role,
            "password": "SafePass123!", "password_confirm": "SafePass123!",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email=f"{role.lower()}@example.com").role, role)

def test_admin_cannot_create_a_user_with_an_unavailable_role(self):
    self.client.force_authenticate(self.admin)
    response = self.client.post("/api/admin/users/", {
        "email": "student@example.com", "first_name": "Student", "last_name": "User",
        "role": User.Role.STUDENT, "password": "SafePass123!", "password_confirm": "SafePass123!",
    }, format="json")
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn("role", response.data)
```

- [ ] **Step 2: Run the account tests to verify the role support is absent**

Run: `DJANGO_SECRET_KEY=test-secret-key DATABASE_URL=sqlite:////tmp/zesa-lms-users.sqlite3 CELERY_BROKER_URL=memory:// CELERY_RESULT_BACKEND=cache+memory:// REDIS_URL=redis://localhost:6379/15 /Users/dazzmurenga/Documents/moodle-5.1.1/.venv/bin/python manage.py test apps.accounts.tests -v 1`

Expected: FAIL because `TRAINER` is not defined and `role` is not writable during user creation.

- [ ] **Step 3: Implement the role, serializer validation, and permission update**

```python
class Role(models.TextChoices):
    TRAINER = "TRAINER", "Trainer"
    LECTURER = "LECTURER", "Lecturer"

class UserCreateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=[User.Role.TRAINER, User.Role.LECTURER])
```

Add the migration that alters `User.role` choices, and include `User.Role.TRAINER` in `CanManageTraining`.

- [ ] **Step 4: Run the account tests and confirm active lecturers remain selectable**

Run: the Task 1 test command.

Expected: PASS, including the existing deactivation test that verifies `/api/admin/lecturers/` excludes inactive lecturers.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts
git commit -m "feat: add trainer role to user management"
```

### Task 2: Give trainers safe ownership of course configuration

**Files:**
- Modify: `backend/apps/accounts/permissions.py`
- Modify: `backend/apps/courses/views.py`
- Modify: `backend/apps/courses/tests.py`

**Interfaces:**
- Consumes: authenticated role in request and existing `POST /api/courses/training/course-types/` and `POST /api/courses/training/certification-types/` endpoints.
- Produces: admins, superadmins, and trainers can manage taxonomy; lecturers can continue managing their assigned course operations but receive `403` when changing shared Settings.

- [ ] **Step 1: Write the failing configuration authorization tests**

```python
def test_trainer_can_create_course_type_and_its_certificate_type(self):
    self.client.force_authenticate(self.trainer)
    course_type = self.client.post("/api/courses/training/course-types/", {
        "code": "HEXCO", "name": "HEXCO"
    }, format="json")
    certificate = self.client.post("/api/courses/training/certification-types/", {
        "course_type": course_type.data["id"], "code": "NC", "name": "National Certificate"
    }, format="json")
    self.assertEqual(course_type.status_code, status.HTTP_201_CREATED)
    self.assertEqual(certificate.status_code, status.HTTP_201_CREATED)

def test_lecturer_cannot_change_shared_course_settings(self):
    self.client.force_authenticate(self.lecturer)
    response = self.client.post("/api/courses/training/course-types/", {
        "code": "NEW", "name": "New Type"
    }, format="json")
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

- [ ] **Step 2: Run the course tests to verify the permission boundary fails**

Run: `DJANGO_SECRET_KEY=test-secret-key DATABASE_URL=sqlite:////tmp/zesa-lms-course-settings.sqlite3 CELERY_BROKER_URL=memory:// CELERY_RESULT_BACKEND=cache+memory:// REDIS_URL=redis://localhost:6379/15 /Users/dazzmurenga/Documents/moodle-5.1.1/.venv/bin/python manage.py test apps.courses.tests -v 1`

Expected: FAIL because shared configuration currently uses `CanManageTraining`, which allows lecturers.

- [ ] **Step 3: Implement a dedicated shared-configuration permission**

```python
class CanManageTrainingConfiguration(BasePermission):
    allowed_roles = (User.Role.ADMIN, User.Role.SUPERADMIN, User.Role.TRAINER)

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)
```

Use it on `DepartmentViewSet`, `CourseTypeViewSet`, `CertificationTypeViewSet`, `GradeBandViewSet`, `QualificationProfileViewSet`, and `QualificationRequirementViewSet`.

- [ ] **Step 4: Run the course tests**

Run: the Task 2 test command.

Expected: PASS, including the existing validation that rejects certificate types from a different course type.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts/permissions.py backend/apps/courses/views.py backend/apps/courses/tests.py
git commit -m "feat: secure training configuration for trainers"
```

### Task 3: Build the role-aware user and Settings screens

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/app/admin/users/page.tsx`
- Modify: `frontend/src/components/layout/AdminLayout.tsx`
- Create: `frontend/src/app/admin/settings/page.tsx`

**Interfaces:**
- Consumes: `GET` and `POST /api/admin/users/`, `GET` and `POST /api/courses/training/course-types/`, `GET` and `POST /api/courses/training/certification-types/`.
- Produces: a create-user modal with a required Trainer/Lecturer selector; a Settings page where an authorized user creates course types and certificate options linked to each type.

- [ ] **Step 1: Extend frontend API types**

```ts
export interface CourseType {
  id: number
  code: string
  name: string
  description: string
  is_active: boolean
}

export interface CertificationType {
  id: number
  course_type: number
  code: string
  name: string
  description: string
  is_active: boolean
}
```

Add `'TRAINER'` to `User['role']`.

- [ ] **Step 2: Add the role selector to Create User**

```tsx
<Select label="Role *" value={form.role} onValueChange={(role) => setForm({ ...form, role })}
  options={[{ value: 'TRAINER', label: 'Trainer' }, { value: 'LECTURER', label: 'Lecturer' }]}
  placeholder="Select a role" />
```

Remove the post-creation “Assign Lecturer” action from the primary flow; preserve deactivation/reactivation controls.

- [ ] **Step 3: Create the Settings page**

Render course types with code, name, active status, and a small add form. Under each type, display only its certificate options and allow a new code/name/description to be linked to that type. Link the page from the administration sidebar as `Settings`.

- [ ] **Step 4: Build the frontend**

Run: `npm run build` from `frontend/`.

Expected: successful production build with the user and Settings routes.

- [ ] **Step 5: Commit**

```bash
git add frontend/src
git commit -m "feat: add trainer user and course settings screens"
```

### Task 4: Use configured types and certificates in course creation

**Files:**
- Modify: `frontend/src/components/admin/CourseEditor.tsx`
- Modify: `frontend/src/types/index.ts`

**Interfaces:**
- Consumes: `GET /api/courses/training/course-types/`, `GET /api/courses/training/certification-types/`, and the existing course `course_type_id` / `certification_type_ids` fields.
- Produces: course creation posts one configured `course_type_id` and zero or more selected certificate IDs that all belong to that type.

- [ ] **Step 1: Replace the fixed level selector with a configured course-type selector**

```tsx
<Select label="Course type *" value={form.courseTypeId}
  onValueChange={(value) => {
    setField('courseTypeId', value)
    setCertificationTypeIds([])
  }}
  options={courseTypes.map((item) => ({ value: String(item.id), label: item.name }))}
  placeholder="Select a course type" />
```

Do not send the old `level` field from the form.

- [ ] **Step 2: Show only compatible certificate options**

```tsx
const availableCertificates = certificationTypes.filter(
  (item) => item.course_type === Number(form.courseTypeId),
)
```

Render them as labelled checkboxes and disable the form submit until a course type, category, intake, and at least one active lecturer are selected.

- [ ] **Step 3: Include taxonomy selections in create and update payloads**

```ts
course_type_id: Number(form.courseTypeId),
certification_type_ids: certificationTypeIds,
```

For an existing course, initialize the selected type and certifications from the API response.

- [ ] **Step 4: Build the frontend and run the relevant backend suite**

Run: `npm run build` from `frontend/`.

Run: the Task 2 Django command.

Expected: both pass; course creation continues to reject mismatched certificate types server-side.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/admin/CourseEditor.tsx frontend/src/types/index.ts
git commit -m "feat: configure course type during course creation"
```

### Task 5: Verify the complete administrator workflow

**Files:**
- Test: `backend/apps/accounts/tests.py`
- Test: `backend/apps/courses/tests.py`

**Interfaces:**
- Consumes: completed Tasks 1-4.
- Produces: evidence that a created lecturer appears in the assignment API, trainers can configure course types and certificates, and course APIs accept matching selections.

- [ ] **Step 1: Run the backend regression suite**

Run: `DJANGO_SECRET_KEY=test-secret-key DATABASE_URL=sqlite:////tmp/zesa-lms-trainer-settings.sqlite3 CELERY_BROKER_URL=memory:// CELERY_RESULT_BACKEND=cache+memory:// REDIS_URL=redis://localhost:6379/15 /Users/dazzmurenga/Documents/moodle-5.1.1/.venv/bin/python manage.py test apps.accounts.tests apps.courses.tests apps.applications.tests apps.applications.tests_e2e apps.workflows.tests -v 1`

Expected: all tests pass.

- [ ] **Step 2: Run Django migration validation**

Run: `DJANGO_SECRET_KEY=test-secret-key DATABASE_URL=sqlite:////tmp/zesa-lms-trainer-settings.sqlite3 /Users/dazzmurenga/Documents/moodle-5.1.1/.venv/bin/python manage.py makemigrations --check --dry-run`

Expected: `No changes detected`.

- [ ] **Step 3: Run the production frontend build**

Run: `npm run build` from `frontend/`.

Expected: successful build.

- [ ] **Step 4: Commit any verification-only changes and prepare the stacked pull request**

```bash
git status --short
git push -u origin codex/trainer-users-course-settings
gh pr create --base codex/user-management-notifications --title "feat: configure trainer users and course settings"
```

## Self-Review

- Role creation: Task 1 permits exactly Trainer and Lecturer from the user screen/API.
- Lecturer assignment: existing active-only endpoint is preserved and covered in Task 1; Task 4 consumes it in course creation.
- Configurable levels: Tasks 2-4 reuse `CourseType` as the business-level classification and expose its certificate types in Settings and course creation.
- Existing lecturer operations: Task 2 keeps lecturer course-operation access while protecting shared settings.
- No database data is removed: the legacy generic `Course.level` remains intact and is simply no longer the configuration control.
