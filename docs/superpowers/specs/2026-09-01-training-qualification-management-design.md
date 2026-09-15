# Training Qualification Management Design

## Goal

Allow training administrators to configure departments, course types, certification options, grade points, and entry requirements; use that configuration to guide applications, assess eligibility, rank candidates, and produce course shortlists.

## Scope

This design covers the ZESA training portal operations layer. Moodle remains the learning engine and is not used to calculate admissions eligibility or shortlist applicants.

## Roles

`ADMIN`, `SUPERADMIN`, and `LECTURER` may manage training configuration and courses. In this release, `LECTURER` is the temporary trainer capability. `REVIEWER` may view qualification assessments, filter and rank applications, and override an automated negative result through the existing approval workflow. `STUDENT` may enter and edit their own academic results while the application is editable.

## Data Model

### Training Taxonomy

`Department`

- `id`, `code`, `name`, `is_active`, timestamps.
- `code` is unique and stable for integrations and student IDs.
- Initial migration creates Electrical, Telecommunications, and Mechanical departments from the current fixed choices.

`CourseType`

- `id`, `code`, `name`, `description`, `requires_qualification_assessment`, `is_active`, timestamps.
- Examples: HEXCO, Standard, Short Course.
- A type may have a default qualification profile.

`CertificationType`

- `id`, `course_type`, `code`, `name`, `description`, `is_active`, timestamps.
- Examples: NC / National Certificate and ND / National Diploma under HEXCO.
- Course types may have any number of certification types. Standard and short-course types may have none.

`Course`

- Adds `course_type` (required) and `departments` (optional many-to-many).
- Adds `certification_types` (optional many-to-many), limited to the selected course type's active certification types.
- Adds an optional course-level qualification profile and an optional minimum-points override.
- A course with no departments is available across departments. A course with one or more departments is available only in those departments.

### Configurable Qualification Rules

`GradeBand`

- `id`, `code`, `label`, `rank`, `points`, `is_active`.
- `rank` supports comparisons such as "B or better" independently of the points value.
- `points` is editable by authorised training users. The initial O-Level scale is A=5, B=4, C=3, D=2, E=1, F=0, but the configuration is authoritative after rollout.

`QualificationProfile`

- `id`, `name`, `education_level`, `max_o_level_sittings`, `minimum_total_points`, `prefer_a_level_sciences`, `is_active`, timestamps.
- A profile is reusable by a course type or course.
- Course-level values override inherited defaults without changing the reusable profile.

`QualificationRequirement`

- Belongs to a profile.
- Defines one required subject or one "any of these subjects" group, the education level, minimum grade band, and whether it is mandatory.
- Supports the initial HEXCO rules: Mathematics B or better, English threshold configured by the trainer, and Science threshold configured by the trainer.
- A science group can contain subjects such as Physics, Chemistry, Biology, Integrated Science, and any additional trainer-defined names.

### Application Results and Assessment

`ApplicationAcademicSitting`

- Belongs to an application.
- Stores `education_level` (O_LEVEL or A_LEVEL), `sitting_number`, examination year, and optional examination session.
- O-Level sitting number is used for the configurable maximum-sittings check.

`ApplicationAcademicResult`

- Belongs to an academic sitting.
- Stores the entered subject name, matched configured subject/group where applicable, selected grade band, and a snapshot of the grade label and point value.
- Certificate uploads remain supporting evidence; they do not replace structured results for automation.

`ApplicationQualificationAssessment`

- One current assessment per application.
- Stores `qualifies`, `total_o_level_points`, `has_a_level_sciences`, `failed_rule_codes`, `assessment_summary`, `assessed_at`, and the profile/configuration snapshot used.
- The snapshot makes historic reviewer decisions and reports auditable if a trainer later changes grade points or rules.

The existing application `department` and `hexco_level` string fields remain as compatibility snapshots during migration. New application foreign keys, `selected_department` and `certification_type`, become the authoritative configuration links. New and edited applications keep the legacy values in sync for current reports, student-ID generation, Moodle profile data, and certificate generation.

## Course Setup Flow

The in-portal Add Course and Edit Course pages gain a training classification section:

1. Select course type.
2. Select zero or more departments.
3. Select zero or more certification types when the type has them.
4. Select a qualification profile when the course type requires qualification assessment.
5. Optionally override the course minimum points.
6. Continue using the existing lecturer assignment, Moodle synchronisation, and first-intake setup.

The Training Setup area includes separate managed lists for departments, course types, certification types, grade bands, qualification profiles, and profile rules. It is only visible to Admin, Superadmin, and Lecturer users.

## Application Flow

The student application form supports either selection order:

- **Department first:** the course selector lists active courses linked to that department plus global courses.
- **Course first:** the selected course fills its single linked department automatically. If the course has several linked departments, the student must choose one from that course's allowed departments. If the course has no departments, department remains optional unless the student category requires it.

After course selection:

- The form shows only the selected course's certification types. A course with exactly one option selects it automatically. A course without certification types does not show this field.
- The form shows structured O-Level results and optional A-Level results when the course type requires an assessment.
- The student may add sittings and subject/grade rows. The form stops adding O-Level sittings beyond the configured maximum and explains why.
- The client may show an indicative result, but the server performs the authoritative assessment on save and submit.

The walk-in flow uses the same course, department, certification, and results API. Staff may enter results on behalf of a student.

## Eligibility and Reviewer Workflow

The assessment service runs whenever a relevant application, course, profile, sitting, or result changes, and immediately before a reviewer takes an approval action.

For a qualification-assessed course it:

1. Resolves the selected course's profile and overrides.
2. Checks the maximum O-Level sittings.
3. Checks each configured mandatory subject or subject group against its minimum grade rank.
4. Sums configured O-Level points from the best valid grade for each counted subject according to the configured profile.
5. Detects configured A-Level science subjects for preference ranking.
6. Compares points with the effective course minimum.
7. Saves an auditable assessment and returns the clear outcome `Meets requirements` or `Does not fully meet requirements` with each failed reason.

The system never blocks a reviewer from approving an application. A negative result is shown prominently in the review screen, included in the reviewer audit trail, and can be overridden through the current approval action with an optional override note.

## Filtering, Ranking, and Reports

The Admin/Reviewer applications list gains filters for course type, course, department, certification type, and eligibility result.

Within a course, the default shortlist order is:

1. Applicants with configured A-Level sciences first.
2. Higher O-Level points first.
3. Surname ascending.
4. First name ascending.

The Shortlisting Report is scoped to a selected course and exports the required list format:

`Course, Surname, Name, Points`

The on-screen report also shows the eligibility outcome, A-Level science preference, and failed rules so reviewers can explain the rank. Exported report data includes only the required columns unless a reviewer explicitly chooses a detailed internal report.

## Validation and Error Handling

- A certification type cannot be attached to a course of another course type.
- An inactive department, course type, certification type, grade band, or profile cannot be selected for a new application.
- Qualification profiles with required rules must have a valid minimum grade band.
- Grade-band rank and points may be changed only for future assessments; existing assessment snapshots stay unchanged until an application is intentionally reassessed.
- Changing a course's configuration causes active draft and submitted applications to be reassessed, with reviewer-visible configuration change context.
- A course deletion remains blocked by existing application protections. Deactivating is preferred.

## Testing Strategy

Backend tests cover configuration permissions, department/course filtering in both selection orders, certification option restrictions, server-side eligibility checks, point totals, sitting limits, A-Level preference, reviewer override, ranking, shortlist export, and legacy application migration.

Frontend tests cover dynamic course and department selectors, conditional certification controls, academic-sitting entry, clear eligibility feedback, reviewer filters, and ranked shortlist display.

End-to-end coverage exercises student application, negative assessment notification, reviewer override approval, payment/enrolment, and certificate issuance without changing the existing Moodle learning workflow.
