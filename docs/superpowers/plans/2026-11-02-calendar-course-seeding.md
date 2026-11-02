# 2026 Calendar Course Seeding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe Django command that seeds the cleaned 2026 workbook catalogue and intakes while preserving valid Moodle course links.

**Architecture:** Store reviewed workbook data as a versioned JSON resource. A management command validates the resource, resolves existing Moodle/Django courses idempotently, creates missing Moodle courses, and upserts Django courses and supported month/week schedules.

**Tech Stack:** Django management commands, Django ORM transactions, Moodle REST client, JSON, Django TestCase/mock.

**Spec:** `docs/superpowers/specs/2026-11-02-calendar-course-seeding-design.md`

## Global Constraints

- Never delete courses, applications, enrolments, or referenced schedules.
- Store real Moodle IDs unless explicitly running in `--db-only` mode.
- Rerunning unchanged input must not create duplicates.
- Preserve workbook source locations and exact ranges in schedule notes.

## Review Focus

- Duplicate workbook titles resolve to one stable course.
- Moodle failures do not create broken Django rows.
- Existing Django/Moodle courses are reused.
- Cross-month dates retain their exact range in notes.
- Invalid/TBA dates are reported and skipped.

---

### Task 1: Curated calendar data

**Files:**
- Create: `backend/apps/courses/management/commands/calendar_2026.json`
- Test: `backend/apps/courses/tests/test_seed_calendar_2026.py`

- [ ] Generate deduplicated, normalized course and schedule records from the supplied workbook.
- [ ] Validate record counts, stable keys, source rows, durations, fees, and dates in tests.

### Task 2: Idempotent seed command

**Files:**
- Create: `backend/apps/courses/management/commands/seed_calendar_2026.py`
- Test: `backend/apps/courses/tests/test_seed_calendar_2026.py`

- [ ] Write failing tests for dry-run, Moodle reuse/create, rerun idempotency, and schedule upserts.
- [ ] Implement validation, Moodle resolution, transactional Django upserts, and summary reporting.
- [ ] Run focused tests until they pass.

### Task 3: Full verification and operator steps

**Files:**
- Modify: `docs/ZESA_SINGLE_NODE_KUBERNETES_INSTALL_RUNBOOK.md`

- [ ] Run the complete course test suite.
- [ ] Document dry-run, live execution, verification, and rollback-safe behavior.
