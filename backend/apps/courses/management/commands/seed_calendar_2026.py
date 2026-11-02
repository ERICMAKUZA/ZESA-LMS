from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.courses.models import Course, CourseCategory, CourseSchedule
from apps.courses.services import MoodleClient


SEED_MARKER = "ZNTC 2026 calendar seed"


def normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


class Command(BaseCommand):
    help = "Seed courses and intakes from the curated ZNTC 2026 calendar"
    data_file = Path(__file__).with_name("calendar_2026.json")

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report the import without changing Moodle or Django.",
        )
        parser.add_argument(
            "--db-only",
            action="store_true",
            help="Use deterministic placeholder Moodle IDs for isolated testing.",
        )
        parser.add_argument(
            "--moodle-category-id",
            type=int,
            default=1,
            help="Moodle category ID for newly created courses (default: 1).",
        )
        parser.add_argument(
            "--clear-year",
            action="store_true",
            help="Remove unreferenced schedule rows previously created by this command.",
        )

    def load_data(self) -> dict:
        try:
            payload = json.loads(self.data_file.read_text())
        except FileNotFoundError as exc:
            raise CommandError(f"Calendar data file not found: {self.data_file}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"Calendar data is invalid JSON: {exc}") from exc

        if payload.get("version") != 1:
            raise CommandError("Unsupported calendar data version.")
        if payload.get("year") != 2026:
            raise CommandError("This command only accepts the reviewed 2026 calendar.")
        courses = payload.get("courses")
        if not isinstance(courses, list) or not courses:
            raise CommandError("Calendar data must contain at least one course.")

        shortnames = set()
        for index, course in enumerate(courses, start=1):
            required = {"shortname", "fullname", "summary", "schedules"}
            missing = required.difference(course)
            if missing:
                raise CommandError(
                    f"Course {index} is missing: {', '.join(sorted(missing))}."
                )
            if course["shortname"] in shortnames:
                raise CommandError(f"Duplicate shortname: {course['shortname']}")
            shortnames.add(course["shortname"])
            for schedule in course["schedules"]:
                try:
                    start = date.fromisoformat(schedule["start_date"])
                    end = date.fromisoformat(schedule["end_date"])
                    schedule["source"]
                except (KeyError, TypeError, ValueError) as exc:
                    raise CommandError(
                        f"Invalid schedule for {course['shortname']}: {schedule!r}"
                    ) from exc
                if end < start:
                    raise CommandError(
                        f"Schedule ends before it starts for {course['shortname']}."
                    )
        return payload

    def handle(self, *args, **options):
        payload = self.load_data()
        course_count = len(payload["courses"])
        schedule_count = sum(len(item["schedules"]) for item in payload["courses"])

        for warning in payload.get("warnings", []):
            self.stdout.write(self.style.WARNING(f"Source warning: {warning}"))

        if options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN complete: {course_count} courses and "
                    f"{schedule_count} scheduled intakes validated; no changes made."
                )
            )
            return

        if options["clear_year"]:
            self._clear_seeded_schedules(payload["year"])

        client = None if options["db_only"] else MoodleClient()
        moodle_courses = [] if client is None else client.get_courses()
        moodle_by_shortname = {
            normalise(item.get("shortname", "")): item
            for item in moodle_courses
            if item.get("shortname")
        }
        moodle_by_fullname = {
            normalise(item.get("fullname", "")): item
            for item in moodle_courses
            if item.get("fullname")
        }

        counts = defaultdict(int)
        for item in payload["courses"]:
            created_moodle_id = None
            try:
                moodle_course = None
                if client is not None:
                    moodle_course = moodle_by_shortname.get(
                        normalise(item["shortname"])
                    ) or moodle_by_fullname.get(normalise(item["fullname"]))
                    if moodle_course is None:
                        moodle_course = client.create_course(
                            shortname=item["shortname"],
                            fullname=item["fullname"],
                            category_id=options["moodle_category_id"],
                            summary=item["summary"],
                            visible=True,
                        )
                        created_moodle_id = int(moodle_course["id"])
                        counts["moodle_created"] += 1
                    else:
                        counts["moodle_reused"] += 1

                moodle_id = (
                    self._db_only_moodle_id(item["shortname"])
                    if client is None
                    else int(moodle_course["id"])
                )
                category_id = int(
                    (moodle_course or {}).get(
                        "categoryid", options["moodle_category_id"]
                    )
                )
                category_name = (moodle_course or {}).get("categoryname") or (
                    f"Moodle category {category_id}"
                )

                with transaction.atomic():
                    course, created, changed = self._upsert_course(
                        item, moodle_id, category_id, category_name
                    )
                    course_result = (
                        "courses_created"
                        if created
                        else "courses_updated"
                        if changed
                        else "courses_unchanged"
                    )
                    counts[course_result] += 1
                    created_schedules, updated_schedules = self._upsert_schedules(
                        course, item["schedules"]
                    )
                    counts["schedules_created"] += created_schedules
                    counts["schedules_updated"] += updated_schedules
            except Exception as exc:
                counts["failed"] += 1
                if created_moodle_id is not None and client is not None:
                    try:
                        client.delete_course(created_moodle_id)
                    except Exception as cleanup_exc:
                        self.stderr.write(
                            self.style.ERROR(
                                f"Could not remove Moodle course {created_moodle_id} "
                                f"after rollback: {cleanup_exc}"
                            )
                        )
                self.stderr.write(
                    self.style.ERROR(f"Failed {item['shortname']}: {exc}")
                )

        summary = " | ".join(
            f"{label}: {counts[key]}"
            for key, label in (
                ("courses_created", "courses created"),
                ("courses_updated", "courses updated"),
                ("courses_unchanged", "courses unchanged"),
                ("schedules_created", "schedules created"),
                ("schedules_updated", "schedules updated"),
                ("moodle_created", "Moodle created"),
                ("moodle_reused", "Moodle reused"),
                ("failed", "failed"),
            )
        )
        if counts["failed"]:
            raise CommandError(f"Calendar import completed with failures. {summary}")
        self.stdout.write(self.style.SUCCESS(f"Calendar import complete. {summary}"))

    def _find_course(self, item: dict, moodle_id: int) -> Course | None:
        course = Course.objects.filter(moodle_course_id=moodle_id).first()
        if course:
            return course
        course = Course.objects.filter(shortname=item["shortname"]).first()
        if course:
            return course
        wanted_name = normalise(item["fullname"])
        return next(
            (
                candidate
                for candidate in Course.objects.all()
                if normalise(candidate.fullname) == wanted_name
            ),
            None,
        )

    def _upsert_course(
        self,
        item: dict,
        moodle_id: int,
        category_id: int,
        category_name: str,
    ) -> tuple[Course, bool, bool]:
        category, _ = CourseCategory.objects.get_or_create(
            moodle_id=category_id,
            defaults={"name": category_name},
        )

        course = self._find_course(item, moodle_id)
        created = course is None
        if created:
            course = Course(moodle_course_id=moodle_id, max_capacity=20)

        values = {
            "moodle_course_id": moodle_id,
            "shortname": item["shortname"],
            "fullname": item["fullname"],
            "summary": item["summary"],
            "duration_days": item.get("duration_days"),
            "level": item.get("level"),
            "price": Decimal(item["price"]) if item.get("price") else None,
            "category": category,
            "is_active": True,
            "requires_approval": True,
        }
        changed_fields = []
        for field, value in values.items():
            if getattr(course, field) != value:
                setattr(course, field, value)
                changed_fields.append(field)
        if created:
            course.save()
        elif changed_fields:
            course.save(update_fields=[*changed_fields, "updated_at"])
        return course, created, bool(changed_fields)

    def _upsert_schedules(
        self, course: Course, schedules: list[dict]
    ) -> tuple[int, int]:
        grouped = defaultdict(list)
        for item in schedules:
            start = date.fromisoformat(item["start_date"])
            grouped[(start.year, start.month, self._week_in_month(start))].append(item)

        created_count = 0
        updated_count = 0
        for (year, month, week), entries in grouped.items():
            details = " ; ".join(
                f"{entry['start_date']} to {entry['end_date']} ({entry['source']})"
                for entry in sorted(entries, key=lambda value: value["start_date"])
            )
            notes = f"{SEED_MARKER} | Exact dates: {details}"
            schedule, created = CourseSchedule.objects.get_or_create(
                course=course,
                year=year,
                month=month,
                week_in_month=week,
                defaults={
                    "max_capacity": course.max_capacity or 20,
                    "status": "OPEN",
                    "notes": notes,
                },
            )
            if created:
                created_count += 1
            elif schedule.notes != notes and (
                not schedule.notes or SEED_MARKER in schedule.notes
            ):
                schedule.notes = notes
                schedule.save(update_fields=["notes"])
                updated_count += 1
        return created_count, updated_count

    def _clear_seeded_schedules(self, year: int) -> None:
        deleted = kept = 0
        schedules = CourseSchedule.objects.filter(
            year=year, notes__contains=SEED_MARKER
        )
        for schedule in schedules:
            if schedule.enrollments.exists() or schedule.attendance_deferrals.exists():
                kept += 1
                continue
            schedule.delete()
            deleted += 1
        self.stdout.write(
            f"Cleared {deleted} unreferenced seeded schedules; kept {kept} referenced."
        )

    @staticmethod
    def _week_in_month(value: date) -> int:
        first = value.replace(day=1)
        days_until_monday = (7 - first.weekday()) % 7
        first_monday = first + timedelta(days=days_until_monday)
        week = ((value - first_monday).days // 7) + 1
        return max(1, min(4, week))

    @staticmethod
    def _db_only_moodle_id(shortname: str) -> int:
        digest = hashlib.sha1(shortname.encode()).hexdigest()
        return 9_000_000 + (int(digest[:8], 16) % 900_000)
