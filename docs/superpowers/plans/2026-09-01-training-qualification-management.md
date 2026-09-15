# Training Qualification Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver trainer-managed course classification and qualification rules that guide student and walk-in applications, assess eligibility, rank applicants, and generate auditable course shortlists.

**Architecture:** Extend the existing `courses` app with the reusable training taxonomy and course configuration, and extend `applications` with structured academic results, an immutable assessment snapshot, and an assessment service. Keep Moodle as the learning engine: the portal owns admissions configuration and decisions, then continues to use the existing payment, enrolment, notification, and Moodle synchronisation paths. Reuse the existing REST API, admin portal pages, and reviewer workflow rather than introducing a separate admissions application.

**Tech Stack:** Django 5, Django REST Framework, django-filter, PostgreSQL in UAT, React/Next.js/TypeScript, existing Moodle REST client, Kubernetes/Argo CD deployment.

**Spec:** `/Users/dazzmurenga/Documents/ZESA-LMS/docs/superpowers/specs/2026-09-01-training-qualification-management-design.md`

## Global Constraints

- Implement the deployable application in `/Users/dazzmurenga/Documents/moodle-5.1.1`; the design and this plan remain in `/Users/dazzmurenga/Documents/ZESA-LMS/docs/superpowers/`.
- `ADMIN`, `SUPERADMIN`, and `LECTURER` can manage training configuration in this release; `LECTURER` is the temporary trainer capability until RBAC replaces it.
- `REVIEWER` can view qualification results, filter/rank applications, and approve a negative result with an optional override note; the system never blocks that approval.
- `STUDENT` can edit structured results only while their application is editable.
- Preserve `Application.department` and `Application.hexco_level` as synchronised legacy snapshots. `selected_department` and `certification_type` are the authoritative relationships.
- `GradeBand.rank` is used for pass-threshold comparisons; `GradeBand.points` is used for ranking. Existing assessment snapshots never change when configuration changes.
- An inactive configuration record cannot be selected for a new course or application. Prefer deactivation over deleting referenced records.
- A course without departments is global. A course with departments is selectable only in those departments.
- The exact negative eligibility copy is `Does not fully meet requirements`; the positive copy is `Meets requirements`.
- Do not change the existing Moodle creation, update, payment-to-enrolment, certificate, or learning workflows except to pass through the already maintained legacy application fields.
- Run backend tests with `/Users/dazzmurenga/Documents/moodle-5.1.1/.venv/bin/python`; run frontend validation with `npm run build` from the frontend directory.
- UAT is protected. Push implementation to a release branch, open or update a pull request to `uat`, and deploy only after the required review and successful checks.

---

## File Structure

- `backend/apps/courses/models.py` - training taxonomy models and course classification/profile relationships.
- `backend/apps/courses/migrations/0008_training_taxonomy_and_course_configuration.py` - schema, legacy department seed, and initial course-type/profile/grade configuration.
- `backend/apps/courses/serializers.py` - public selection metadata plus protected configuration and course edit serializers.
- `backend/apps/courses/views.py` and `backend/apps/courses/urls.py` - management CRUD and filtered active course-selection endpoints.
- `backend/apps/courses/tests.py` - taxonomy permissions, invariants, course filtering, and course administration tests.
- `backend/apps/accounts/permissions.py` - `CanManageTraining` permission used by both course and qualification configuration endpoints.
- `backend/apps/applications/models.py` - authoritative application references, academic sitting/result models, assessment model, and approval override audit fields.
- `backend/apps/applications/migrations/0011_training_qualification_assessment.py` - application schema and legacy-value backfill.
- `backend/apps/applications/services/qualification.py` - deterministic assessment and ranking functions with no HTTP/UI dependencies.
- `backend/apps/applications/serializers.py`, `views.py`, `urls.py`, and `filters.py` - student/walk-in result APIs, reviewer assessment output, filters, and override action.
- `backend/apps/applications/tests.py` - assessment, selection validation, permission, override, and migration-facing regression tests.
- `backend/apps/reports/views.py`, `serializers.py`, and `urls.py` - course-scoped shortlist response and CSV export.
- `frontend/src/types/index.ts` and `frontend/src/lib/api.ts` - shared types and typed API methods for all new endpoints.
- `frontend/src/components/AcademicResultsEditor.tsx` - reusable O-Level/A-Level sitting and grade entry control used by self-service and walk-in forms.
- `frontend/src/components/WalkInModal.tsx` - staff capture uses the same dynamic selection/results data as students.
- `frontend/src/components/layout/AdminLayout.tsx` - Training Setup navigation for the three temporary training-management roles.
- `frontend/src/app/applications/new/page.tsx` - student course/department selection and academic result capture.
- `frontend/src/app/admin/training/page.tsx` - training configuration workspace with department, type, certification, grade-band, profile, and requirement management.
- `frontend/src/app/admin/courses/new/page.tsx`, `frontend/src/app/admin/courses/[id]/page.tsx`, and `frontend/src/components/admin/CourseEditor.tsx` - course classification and qualification controls.
- `frontend/src/app/admin/applications/page.tsx` and `frontend/src/app/admin/applications/[id]/page.tsx` - reviewer filters, visible assessment, override entry, and ranked course view.
- `frontend/src/app/admin/reports/shortlist/page.tsx` - course shortlist display and export control.

## Task 1: Add Training Taxonomy, Course Configuration, and Authorization

**Files:**
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/accounts/permissions.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/courses/models.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/courses/serializers.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/courses/views.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/courses/urls.py`
- Create: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/courses/migrations/0008_training_taxonomy_and_course_configuration.py`
- Test: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/courses/tests.py`

**Interfaces:**
- Consumes: `Course` and `AdminCourseViewSet` in `apps.courses`; `User.Role` in `apps.accounts.models`.
- Produces: `CanManageTraining`, `Department`, `CourseType`, `CertificationType`, `GradeBand`, `QualificationProfile`, `QualificationRequirement`; `GET /api/courses/training/selection/`; CRUD endpoints below `/api/courses/training/`; `Course.course_type`, `Course.departments`, `Course.certification_types`, `Course.qualification_profile`, and `Course.minimum_points_override`.

- [ ] **Step 1: Write the failing authorization and taxonomy tests**

```python
def test_lecturer_can_manage_training_configuration(self):
    self.client.force_authenticate(self.lecturer)
    response = self.client.post(
        "/api/courses/training/departments/",
        {"code": "ELECTRICAL", "name": "Electrical Engineering"},
        format="json",
    )
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)

def test_student_cannot_manage_training_configuration(self):
    self.client.force_authenticate(self.student)
    response = self.client.post(
        "/api/courses/training/departments/",
        {"code": "ELECTRICAL", "name": "Electrical Engineering"},
        format="json",
    )
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

def test_course_rejects_certification_from_another_course_type(self):
    course = CourseFactory(course_type=self.hexco_type)
    with self.assertRaises(ValidationError):
        course.certification_types.set([self.standard_certificate])
        course.full_clean()
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run from `/Users/dazzmurenga/Documents/moodle-5.1.1/backend`:

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py test apps.courses.tests -v 2
```

Expected: failures because the permission, taxonomy models, and endpoints do not exist.

- [ ] **Step 3: Implement the permission, models, migrations, serializers, and endpoints**

Add this permission and use it for every management endpoint and course create/update view:

```python
class CanManageTraining(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                User.Role.ADMIN,
                User.Role.SUPERADMIN,
                User.Role.LECTURER,
            )
        )
```

Define the taxonomy with unique stable `code` fields and `is_active`; define `CertificationType.course_type` and `QualificationRequirement.profile` foreign keys. Add `Course.clean()` validation that every attached certification type belongs to `course.course_type`, and expose nested read values plus writable ID fields through `CourseSerializer`. Register explicit viewsets for departments, course types, certification types, grade bands, profiles, and requirements under `training/`; return only active records from the unauthenticated selection endpoint.

Create a data migration that seeds the three legacy departments, `HEXCO`, `STANDARD`, and `SHORT_COURSE`, `NC` and `ND` under `HEXCO`, the A-to-F bands with ranks `6` through `1` and points `5` through `0`, and an active reusable `HEXCO_DEFAULT` profile. Do not attach a profile or course type to existing courses automatically unless the migration can make an unambiguous choice; seed records first so administrators can classify them safely.

- [ ] **Step 4: Run focused tests and create the migration checks**

Run:

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py makemigrations --check
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py test apps.courses.tests -v 2
```

Expected: no pending model changes and all course tests pass.

- [ ] **Step 5: Commit the independently testable taxonomy foundation**

```bash
git add backend/apps/accounts/permissions.py backend/apps/courses
git commit -m "feat: add training course configuration"
```

## Task 2: Add Authoritative Application Qualification Data and Assessment Service

**Files:**
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/models.py`
- Create: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/services/__init__.py`
- Create: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/services/qualification.py`
- Create: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/migrations/0011_training_qualification_assessment.py`
- Test: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/tests.py`

**Interfaces:**
- Consumes: taxonomy models from `apps.courses.models` and the existing `Application` state machine.
- Produces: `Application.selected_department`, `Application.certification_type`, `ApplicationAcademicSitting`, `ApplicationAcademicResult`, `ApplicationQualificationAssessment`, `ApplicationQualificationOverride`; `assess_application(application: Application) -> ApplicationQualificationAssessment`; `shortlist_ordering()`.

- [ ] **Step 1: Write failing unit tests for eligibility, audit snapshots, and ranking**

```python
def test_assessment_requires_maths_b_or_better_and_minimum_points(self):
    application = ApplicationFactory(course=self.hexco_course)
    add_o_level_result(application, subject="Mathematics", grade="C")
    add_o_level_result(application, subject="English", grade="B")
    add_o_level_result(application, subject="Physics", grade="B")

    assessment = assess_application(application)

    self.assertFalse(assessment.qualifies)
    self.assertIn("MATHS_MINIMUM_GRADE", assessment.failed_rule_codes)
    self.assertEqual(assessment.assessment_summary, "Does not fully meet requirements")

def test_assessment_uses_best_grade_once_per_o_level_subject(self):
    application = ApplicationFactory(course=self.hexco_course)
    add_o_level_result(application, sitting_number=1, subject="Mathematics", grade="B")
    add_o_level_result(application, sitting_number=2, subject="Mathematics", grade="A")

    assessment = assess_application(application)

    self.assertEqual(assessment.total_o_level_points, 5)

def test_shortlist_prefers_a_level_sciences_then_points_then_name(self):
    ranked = list(shortlist_ordering(Application.objects.filter(course=self.hexco_course)))
    self.assertEqual([item.applicant.last_name for item in ranked], ["Zulu", "Alpha", "Beta"])
```

- [ ] **Step 2: Run the assessment tests to verify they fail**

Run:

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py test apps.applications.tests -v 2
```

Expected: import errors for `assess_application`, missing application qualification models, and missing relationships.

- [ ] **Step 3: Implement data models, compatibility synchronisation, and the pure assessment service**

Add the authoritative foreign keys with `SET_NULL` and `related_name` values, while retaining the existing strings:

```python
selected_department = models.ForeignKey(
    "courses.Department", null=True, blank=True,
    on_delete=models.SET_NULL, related_name="applications",
)
certification_type = models.ForeignKey(
    "courses.CertificationType", null=True, blank=True,
    on_delete=models.SET_NULL, related_name="applications",
)
```

Create sitting/result models with an `education_level` choice of `O_LEVEL` and `A_LEVEL`. Store `grade_label_snapshot` and `points_snapshot` on each result when it is saved. Create one `ApplicationQualificationAssessment` per application with `JSONField` values for `failed_rule_codes` and `configuration_snapshot`; create `ApplicationQualificationOverride` with reviewer, note, and timestamp.

Implement `assess_application` as a deterministic service. It must resolve the course-level profile first, otherwise the course type default profile; calculate the effective minimum from `course.minimum_points_override` otherwise `profile.minimum_total_points`; check configured O-Level sitting count; evaluate all mandatory subject/group rules by grade rank; sum one best O-Level grade per normalised subject; detect configured A-Level science-group matches; save the full grade/profile/rule snapshot and the exact positive/negative summary. Return an automatically qualifying assessment only when `course.course_type.requires_qualification_assessment` is false.

Add `Application.sync_legacy_training_fields()` and call it from validated serializers before save, setting `department` to the selected department name/code convention used by legacy consumers and `hexco_level` to `certification_type.code` when present. The migration must map only known legacy department strings to the seeded departments and map `NC`/`ND` to seeded certification types; leave unmatched values intact and null authoritative links rather than guessing.

- [ ] **Step 4: Run unit tests and migration validation**

Run:

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py makemigrations --check
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py test apps.applications.tests -v 2
```

Expected: all assessment tests pass, and `makemigrations --check` reports no changes.

- [ ] **Step 5: Commit the assessment domain layer**

```bash
git add backend/apps/applications/models.py backend/apps/applications/services backend/apps/applications/migrations/0011_training_qualification_assessment.py backend/apps/applications/tests.py
git commit -m "feat: assess application qualifications"
```

## Task 3: Expose Validated Application, Walk-in, and Reviewer APIs

**Files:**
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/serializers.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/views.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/urls.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/filters.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/tests.py`

**Interfaces:**
- Consumes: `assess_application`, application qualification models, and `GET /api/courses/training/selection/` from Tasks 1-2.
- Produces: validated application payload fields `selected_department_id`, `certification_type_id`, and `academic_sittings`; qualification assessment output on student/admin serializers; `POST /api/admin/applications/{id}/override-qualification/`; filters `course_type`, `selected_department`, `certification_type`, and `eligibility`.

- [ ] **Step 1: Write failing API tests for two-way selection, result validation, and reviewer override**

```python
def test_student_can_submit_course_first_when_course_has_one_department(self):
    payload = application_payload(
        course=self.single_department_course.id,
        selected_department_id=None,
        certification_type_id=self.nc.id,
        academic_sittings=valid_o_level_sittings(),
    )
    response = self.client.post("/api/my-applications/", payload, format="json")
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertEqual(response.data["selected_department"]["id"], self.electrical.id)

def test_student_cannot_submit_department_outside_selected_course(self):
    response = self.client.post(
        "/api/my-applications/",
        application_payload(
            course=self.single_department_course.id,
            selected_department_id=self.telecoms.id,
            certification_type_id=self.nc.id,
            academic_sittings=valid_o_level_sittings(),
        ),
        format="json",
    )
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn("selected_department_id", response.data)

def test_reviewer_can_override_negative_qualification_with_note(self):
    self.client.force_authenticate(self.reviewer)
    response = self.client.post(
        f"/api/admin/applications/{self.negative_application.id}/override-qualification/",
        {"note": "Relevant industry experience verified."},
        format="json",
    )
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertTrue(ApplicationQualificationOverride.objects.filter(application=self.negative_application).exists())
```

- [ ] **Step 2: Run the focused API tests to verify they fail**

Run:

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py test apps.applications.tests -v 2
```

Expected: missing serializer fields, actions, and filters.

- [ ] **Step 3: Implement transactional serializers, reassessment hooks, endpoints, and filters**

Create input serializers whose nested sitting payload is:

```python
{
    "education_level": "O_LEVEL",
    "sitting_number": 1,
    "exam_year": 2025,
    "exam_session": "NOVEMBER",
    "results": [{"subject": "Mathematics", "grade_band_id": 2}],
}
```

Validate active course type, selected department membership, certification type membership, grade-band activity, certification visibility, and profile O-Level cap server-side. If course-first selection has one department, populate it; if it has many, require a submitted member; if it is global, allow null unless an existing student-category rule still requires a department. Use `transaction.atomic()` to replace editable sitting/result rows, synchronise legacy fields, and call `assess_application` after create/update and immediately before `approve()`.

Return nested assessment, selected department, certification type, and structured results in all student/admin/lecturer detail serializers. Add the override action with `IsAdminOrReviewer` permission, save an override audit record, and append the note to status history without changing the automatic assessment. Add `django-filter` filters that map `eligibility=MEETS` to `qualification_assessment__qualifies=True` and `eligibility=DOES_NOT_MEET` to `False`.

- [ ] **Step 4: Run application tests and the affected workflow regression suite**

Run:

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite REDIS_URL=redis://localhost:6379/0 CELERY_BROKER_URL=redis://localhost:6379/0 CELERY_RESULT_BACKEND=redis://localhost:6379/1 ../.venv/bin/python manage.py test apps.applications.tests apps.workflows -v 2
```

Expected: application qualification tests and existing workflow tests pass. Do not alter notification task semantics to make a Redis-less end-to-end test pass.

- [ ] **Step 5: Commit the validated application API**

```bash
git add backend/apps/applications/serializers.py backend/apps/applications/views.py backend/apps/applications/urls.py backend/apps/applications/filters.py backend/apps/applications/tests.py
git commit -m "feat: capture and review qualification results"
```

## Task 4: Add Shortlist Ranking and Export

**Files:**
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/reports/views.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/reports/serializers.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/reports/urls.py`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/tests.py`

**Interfaces:**
- Consumes: `shortlist_ordering(queryset)` and persisted assessment data from Task 2.
- Produces: `GET /api/reports/shortlist/?course=<course_id>&detailed=false`; CSV columns exactly `Course,Surname,Name,Points`; detailed on-screen eligibility data.

- [ ] **Step 1: Write failing shortlist response and CSV tests**

```python
def test_shortlist_exports_required_columns_in_rank_order(self):
    self.client.force_authenticate(self.reviewer)
    response = self.client.get(f"/api/reports/shortlist/?course={self.course.id}&format=csv")

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response["Content-Type"], "text/csv")
    rows = list(csv.reader(io.StringIO(response.content.decode())))
    self.assertEqual(rows[0], ["Course", "Surname", "Name", "Points"])
    self.assertEqual(rows[1][1:3], ["Zulu", "Ada"])

def test_shortlist_json_exposes_review_context_without_expanding_default_csv(self):
    response = self.client.get(f"/api/reports/shortlist/?course={self.course.id}")
    self.assertIn("eligibility", response.data["results"][0])
    self.assertIn("failed_rule_codes", response.data["results"][0])
```

- [ ] **Step 2: Run the report tests to verify they fail**

Run:

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py test apps.applications.tests -v 2
```

Expected: 404 or missing response fields.

- [ ] **Step 3: Implement the reviewer-only shortlist endpoint**

Use `shortlist_ordering(Application.objects.filter(course_id=course_id))` and `select_related` assessment/applicant data. Return the selection timestamp, course metadata, and rows with surname, first name, points, eligibility outcome, A-Level science preference, failed rules, and override state. Emit a CSV only when `format=csv`; use the exact four required columns by default and add detailed internal columns only when `detailed=true` is supplied by an authorised reviewer.

- [ ] **Step 4: Run report tests and the full affected backend suite**

Run:

```bash
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite REDIS_URL=redis://localhost:6379/0 CELERY_BROKER_URL=redis://localhost:6379/0 CELERY_RESULT_BACKEND=redis://localhost:6379/1 ../.venv/bin/python manage.py test apps.courses apps.applications.tests apps.workflows -v 2
```

Expected: all targeted tests pass.

- [ ] **Step 5: Commit shortlist delivery**

```bash
git add backend/apps/reports backend/apps/applications/tests.py
git commit -m "feat: add qualification shortlist report"
```

## Task 5: Build Training Setup and Course Classification UI

**Files:**
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/types/index.ts`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/lib/api.ts`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/components/layout/AdminLayout.tsx`
- Create: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/app/admin/training/page.tsx`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/components/admin/CourseEditor.tsx`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/app/admin/courses/new/page.tsx`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/app/admin/courses/[id]/page.tsx`

**Interfaces:**
- Consumes: Task 1 endpoints and active taxonomy response.
- Produces: `/admin/training` for allowed roles; course payload fields `course_type_id`, `department_ids`, `certification_type_ids`, `qualification_profile_id`, `minimum_points_override`.

- [ ] **Step 1: Write failing frontend tests or component-level assertions for role navigation and conditional fields**

```tsx
it("shows Training Setup to lecturers and hides it from reviewers", () => {
  expect(navigationFor({ role: "LECTURER" })).toContainEqual(
    expect.objectContaining({ href: "/admin/training", label: "Training Setup" }),
  );
  expect(navigationFor({ role: "REVIEWER" })).not.toContainEqual(
    expect.objectContaining({ href: "/admin/training" }),
  );
});

it("shows certification choices only for the selected course type", () => {
  render(<CourseEditor courseTypes={courseTypes} certificationTypes={certifications} />);
  fireEvent.change(screen.getByLabelText("Course type"), { target: { value: "HEXCO" } });
  expect(screen.getByLabelText("Certification types")).toBeVisible();
});
```

- [ ] **Step 2: Run the frontend test command available in the repository and verify failure**

Run from `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend`:

```bash
npm test -- --runInBand
```

If the repository has no test script, record that fact in the task PR and use the build validation in Step 4; do not introduce a test framework solely for this release.

- [ ] **Step 3: Implement typed configuration APIs and the management screens**

Define `Department`, `CourseType`, `CertificationType`, `GradeBand`, `QualificationProfile`, and `QualificationRequirement` interfaces in `types/index.ts`, then add typed list/create/update/deactivate methods in `lib/api.ts`. Add a single Training Setup page with focused tabs or sections for each list, inline create/edit forms, explicit active/inactive state, and profile rules including subject groups, education level, required flag, and minimum grade band.

Extend `CourseEditor` to load active types and profiles, show departments as a multi-select, filter certification choices to the selected type, require a profile only when the type requires assessment, and expose the optional minimum-points override. Preserve existing lecturer assignment, Moodle category, first intake, and create/update calls. Add Training Setup to the `ADMIN`, `SUPERADMIN`, and lecturer navigation only.

- [ ] **Step 4: Run static validation and production build**

Run:

```bash
npm run lint
npm run build
```

Expected: no TypeScript, lint, or production-build errors.

- [ ] **Step 5: Commit the configuration UI**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts frontend/src/components/layout/AdminLayout.tsx frontend/src/components/admin/CourseEditor.tsx frontend/src/app/admin/training frontend/src/app/admin/courses
git commit -m "feat: manage training qualification configuration"
```

## Task 6: Build Student and Walk-in Application Qualification Capture

**Files:**
- Create: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/components/AcademicResultsEditor.tsx`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/app/applications/new/page.tsx`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/components/WalkInModal.tsx`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/types/index.ts`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/lib/api.ts`

**Interfaces:**
- Consumes: `GET /api/courses/training/selection/` and Task 3 application serializer input/output.
- Produces: `AcademicResultsEditor` with `value: AcademicSittingInput[]`, `onChange(value: AcademicSittingInput[]): void`, and `maxOLevelSittings?: number`; student and walk-in payloads carrying authoritative IDs and `academic_sittings`.

- [ ] **Step 1: Write failing component tests for both selection orders and results rules**

```tsx
it("filters courses after department selection and includes global courses", async () => {
  render(<ApplicationForm selection={selection} />);
  await user.selectOptions(screen.getByLabelText("Department"), "ELECTRICAL");
  expect(screen.getByRole("option", { name: "Electrical Installation" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "Generic Safety" })).toBeInTheDocument();
  expect(screen.queryByRole("option", { name: "Telecoms Fibre" })).not.toBeInTheDocument();
});

it("fills a course's sole department and preselects its sole certification", async () => {
  render(<ApplicationForm selection={selection} />);
  await user.selectOptions(screen.getByLabelText("Course"), "HEXCO Electrical");
  expect(screen.getByLabelText("Department")).toHaveValue("ELECTRICAL");
  expect(screen.getByLabelText("Certification type")).toHaveValue("NC");
});

it("does not add an O-Level sitting beyond the active profile limit", async () => {
  render(<AcademicResultsEditor maxOLevelSittings={2} value={twoOLevelSittings} onChange={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "Add O-Level sitting" })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run the frontend test command to verify failure**

Run:

```bash
npm test -- --runInBand
```

Expected: missing component and dynamic controls.

- [ ] **Step 3: Implement a shared, server-aligned selection and results experience**

Fetch the active selection catalog once in the application form. Support course-first and department-first choices exactly as the API validates: show department-filtered and global courses; set a sole linked department automatically; require a selected member if a course has multiple departments; leave global department optional unless the existing category rule requires it. Only show certification when the selected course has certification options and preselect the only option.

Implement `AcademicResultsEditor` with separate O-Level and optional A-Level sitting lists, an exam year/session, subject text field, and grade-band selector loaded from the active catalog. Limit the add-O-Level action from the profile maximum and show the reason inline. Reuse this component and the same catalog transforms in `WalkInModal`; remove its hard-coded departments and NC/ND controls. Present the returned server assessment as indicative guidance, never as a client-side approval gate.

- [ ] **Step 4: Run the application frontend validation**

Run:

```bash
npm run lint
npm run build
```

Expected: frontend compiles and the production build succeeds.

- [ ] **Step 5: Commit application capture UI**

```bash
git add frontend/src/components/AcademicResultsEditor.tsx frontend/src/components/WalkInModal.tsx frontend/src/app/applications/new/page.tsx frontend/src/types/index.ts frontend/src/lib/api.ts
git commit -m "feat: capture configurable qualification results"
```

## Task 7: Build Reviewer Assessment, Filtering, and Shortlist UI

**Files:**
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/app/admin/applications/page.tsx`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/app/admin/applications/[id]/page.tsx`
- Create: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/app/admin/reports/shortlist/page.tsx`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/lib/api.ts`
- Modify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/src/types/index.ts`

**Interfaces:**
- Consumes: Task 3 assessment/filter/override APIs and Task 4 shortlist response.
- Produces: reviewer filter query fields `course_type`, `course`, `selected_department`, `certification_type`, `eligibility`; override request `{ note: string }`; shortlist browser and CSV download.

- [ ] **Step 1: Write failing UI assertions for assessment visibility and override**

```tsx
it("shows the exact negative qualification outcome and failed rules", () => {
  render(<ApplicationReview application={negativeApplication} />);
  expect(screen.getByText("Does not fully meet requirements")).toBeVisible();
  expect(screen.getByText("Mathematics: minimum grade B" )).toBeVisible();
});

it("allows a reviewer to record an approval override note", async () => {
  render(<ApplicationReview application={negativeApplication} />);
  await user.click(screen.getByRole("button", { name: "Override qualification result" }));
  await user.type(screen.getByLabelText("Override note"), "Experience verified");
  await user.click(screen.getByRole("button", { name: "Save override" }));
  expect(api.overrideQualification).toHaveBeenCalledWith(negativeApplication.id, { note: "Experience verified" });
});
```

- [ ] **Step 2: Run the frontend test command to verify failure**

Run:

```bash
npm test -- --runInBand
```

Expected: missing assessment components, filters, override action, and shortlist page.

- [ ] **Step 3: Implement reviewer-facing status, controls, and ranked shortlist**

Add filters to the applications list for course type, course, department, certification type, and eligibility. Display assessment outcome, points, A-Level science preference, and an override indicator in the review detail. Keep the standard approval action available even with a negative outcome; require no override note but offer it before approval and show existing overrides in the audit area.

Create `/admin/reports/shortlist` with a required course selector, ranked rows from the API, and a clearly labelled standard CSV export. Show failed rules and reviewer override context on-screen; keep the standard export at exactly `Course, Surname, Name, Points`, with a separate explicit detailed internal export control.

- [ ] **Step 4: Run final frontend checks**

Run:

```bash
npm run lint
npm run build
```

Expected: clean lint and successful production build.

- [ ] **Step 5: Commit reviewer and report UI**

```bash
git add frontend/src/app/admin/applications frontend/src/app/admin/reports frontend/src/lib/api.ts frontend/src/types/index.ts
git commit -m "feat: review qualification assessments and shortlists"
```

## Task 8: Run Regression, Verify Upgrade Safety, and Release to UAT

**Files:**
- Modify only if verification exposes a reproducible feature regression: the exact source file covered by its new failing test.
- Verify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/courses/tests.py`
- Verify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/applications/tests.py`
- Verify: `/Users/dazzmurenga/Documents/moodle-5.1.1/backend/apps/workflows/`
- Verify: `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend/`

**Interfaces:**
- Consumes: Tasks 1-7 and the existing UAT GitHub Actions/Argo CD pipeline.
- Produces: a reviewed UAT pull request containing migrations, passing targeted tests/build, and a post-deploy evidence checklist.

- [ ] **Step 1: Run migration and backend regression checks against a clean test database**

Run from `/Users/dazzmurenga/Documents/moodle-5.1.1/backend`:

```bash
rm -f /tmp/moodle-qualification-tests.sqlite
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py migrate --noinput
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite REDIS_URL=redis://localhost:6379/0 CELERY_BROKER_URL=redis://localhost:6379/0 CELERY_RESULT_BACKEND=redis://localhost:6379/1 ../.venv/bin/python manage.py test apps.courses apps.applications.tests apps.workflows -v 2
DJANGO_SECRET_KEY=test DATABASE_URL=sqlite:////tmp/moodle-qualification-tests.sqlite ../.venv/bin/python manage.py makemigrations --check
```

Expected: migrations apply, targeted tests pass, and no uncommitted model migration is requested.

- [ ] **Step 2: Run frontend production validation**

Run from `/Users/dazzmurenga/Documents/moodle-5.1.1/frontend`:

```bash
npm run lint
npm run build
```

Expected: both commands exit successfully.

- [ ] **Step 3: Run explicit release acceptance checks in UAT after deployment**

Verify using an Admin/Trainer, Student, and Reviewer account:

```text
1. Create a department, HEXCO type, NC/ND certification types, grade bands, a profile, and Maths/English/Science requirements.
2. Create or edit a course with that type, linked departments, certification choices, profile, minimum points, lecturer, and intake; confirm Moodle course sync remains successful.
3. Submit a student application department-first; submit another course-first; verify global and multi-department rules, NC/ND controls, O-Level cap, and returned eligibility.
4. Register a walk-in using the same course/department/certification/result controls.
5. Review a negative application, filter it by eligibility/course type, save an override note, approve it, then verify existing payment-to-enrolment and Moodle learning access still work.
6. Open the course shortlist, confirm A-Level science then points then surname/name ordering, and download the four-column CSV.
```

- [ ] **Step 4: Create the protected UAT release pull request**

Run from `/Users/dazzmurenga/Documents/moodle-5.1.1` after all feature commits:

```bash
git status --short
git push origin HEAD:codex/training-qualification-management-uat
gh pr create --base uat --head codex/training-qualification-management-uat --title "feat: configurable training qualification management" --body "Implements configurable departments, course types, certification types, grade points, qualification assessment, reviewer override, ranking, and shortlist export. Includes Django migrations and frontend build verification."
```

Expected: a pull request is opened to protected `uat`; do not force-push or bypass required review.

- [ ] **Step 5: Monitor CI, GitOps, and Argo after approval and merge**

Verify the image tag update in the GitOps UAT values file, Argo application health/sync, and readiness of web, worker, and beat pods. Record the source commit, image tag, GitOps commit, Argo state, pod readiness, and the acceptance checks above in the pull request or release note.

## Self-Review

**Spec coverage:**

- Training roles, configured departments/types/certifications/grade points/profiles/rules: Tasks 1 and 5.
- Course classification, optional department links, certification restrictions, profile/points overrides, and retained lecturer/Moodle flow: Tasks 1 and 5.
- Authoritative application relationships and legacy snapshots: Task 2.
- Structured O-Level/A-Level sittings and grade snapshots: Tasks 2, 3, and 6.
- Both selection orders, global/multi-department cases, certification preselection, and walk-in parity: Tasks 3 and 6.
- Automated eligibility, sitting limit, rules, best-grade points, A-Level science preference, and audit snapshot: Task 2.
- Reassessment and reviewer override without blocking approval: Task 3 and Task 7.
- Filters, ranking, standard and detailed shortlist report: Tasks 3, 4, and 7.
- Inactive configuration, no cross-type certification, migration/backfill safety, Moodle/workflow regression, and protected UAT release: Tasks 1, 2, 3, and 8.

**Placeholder scan:** Completed. This plan has no `TODO`, `TBD`, “implement later”, or unspecified-test steps.

**Type consistency:** `assess_application(application)` and `shortlist_ordering(queryset)` are defined in Task 2 and consumed consistently by Tasks 3 and 4. `selected_department_id`, `certification_type_id`, and `academic_sittings` are produced by Task 3 and consumed by Tasks 6 and 7.
