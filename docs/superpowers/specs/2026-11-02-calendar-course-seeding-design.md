# 2026 Calendar Course Seeding Design

## Intent

Provide a repeatable Django management command that seeds the 2026 ZESA NTC
course catalogue and its dated intakes from `Draft Calendar 2026..-1.xlsx`
without requiring that workbook on the deployment server.

## Scope

- Include valid course and service rows from Technical Courses, Non Technical
  Courses, Available on Request, and Consultancy Services.
- Exclude blank rows, headings, and the attendee/contact lists embedded below
  the Consultancy Services table.
- Deduplicate equivalent titles across sheets and prefer the row containing a
  published schedule and concrete fee/duration.
- Create dated 2026 `CourseSchedule` rows where the workbook supplies a date
  range. Skip `TBA` schedule cells and courses with no scheduled dates.
- Record the workbook's exact date range and source sheet/row in schedule notes,
  because the current model stores only month and week rather than exact dates.
- Treat Available on Request and unscheduled Consultancy Services entries as
  active catalogue courses without intakes.

## Command

Add `python manage.py seed_calendar_2026` with these options:

- `--dry-run`: validate and report all intended changes without writing to
  Moodle or Django.
- `--clear-year`: remove only unreferenced 2026 schedule rows before reseeding;
  never delete courses, applications, enrolments, or referenced schedules.
- `--db-only`: allow isolated local/test database seeding with deterministic
  reserved IDs. This option is not for a connected deployment.

The default path creates or reuses matching Moodle courses by short name, then
stores their real Moodle IDs in Django. Existing Django courses are updated by
Moodle ID or stable short name rather than duplicated.

## Normalisation

- Generate stable short names from a curated data module rather than changing
  them on every run.
- Parse days, weeks, months, and years into `duration_days`; report unsupported
  values rather than guessing silently.
- Parse numeric fees as USD decimals and leave `TBA` or blank fees unset.
- Map workbook sections to existing ZNTC course categories. Categories are
  reused by Moodle ID and are not destructively recreated.
- Convert a dated range to the nearest supported `CourseSchedule` month/week,
  retaining the exact range in notes. Cross-month ranges are supported.
- Skip the invalid April `28-31` and September `31-04` entries with warnings
  until the source calendar is corrected.

## Safety And Reporting

- Wrap each Django course/schedule update in a transaction.
- Never use the destructive behavior of the existing `seed_courses` command.
- Report created, updated, unchanged, skipped, and failed counts for Moodle
  courses, Django courses, and schedules.
- A rerun with unchanged input produces no additional records.
- A Moodle failure leaves the corresponding Django course unchanged and is
  reported clearly.

## Approaches Considered

1. **Embedded curated data in a Django command (selected):** deployable,
   reviewable, idempotent, and independent of spreadsheet libraries in
   production.
2. Runtime Excel importer: easier to replace the source file, but carries the
   workbook's formatting errors into production and adds an Excel dependency.
3. Django fixture: compact, but poorly suited to Moodle IDs, deduplication,
   updates, dry runs, and reruns.

## Verification

- Unit tests cover parsing, deduplication, stable short names, schedule mapping,
  dry-run behavior, rerun idempotency, Moodle reuse/creation, and source errors.
- Command-level tests verify that existing courses are updated without deleting
  related data and that schedule uniqueness is preserved.
- Run the course test suite and execute a dry run before using the command in
  the deployed environment.
