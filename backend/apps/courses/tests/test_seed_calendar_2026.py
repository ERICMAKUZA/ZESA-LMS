import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.courses.models import Course, CourseSchedule


class SeedCalendar2026CommandTests(TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.data_path = Path(self.tempdir.name) / "calendar.json"
        self.data_path.write_text(json.dumps({
            "version": 1,
            "year": 2026,
            "courses": [{
                "shortname": "CAL26-TEST-123456",
                "fullname": "Test Calendar Course",
                "duration_days": 5,
                "price": "325.00",
                "category": "Technical Training",
                "summary": "A test course.",
                "source_rows": ["Technical Courses!4"],
                "schedules": [{
                    "start_date": "2026-01-19",
                    "end_date": "2026-01-23",
                    "source": "Technical Courses!D4",
                }],
            }],
            "warnings": [],
        }))

    def run_command(self, *args):
        stdout = StringIO()
        with patch(
            "apps.courses.management.commands.seed_calendar_2026.Command.data_file",
            self.data_path,
        ):
            call_command("seed_calendar_2026", *args, stdout=stdout)
        return stdout.getvalue()

    @patch("apps.courses.management.commands.seed_calendar_2026.MoodleClient")
    def test_dry_run_has_no_database_or_moodle_side_effects(self, client_class):
        output = self.run_command("--dry-run")

        self.assertEqual(Course.objects.count(), 0)
        self.assertEqual(CourseSchedule.objects.count(), 0)
        client_class.assert_not_called()
        self.assertIn("DRY RUN", output)
        self.assertIn("1 course", output)

    def test_db_only_seed_is_idempotent_and_preserves_exact_dates_in_notes(self):
        self.run_command("--db-only")
        self.run_command("--db-only")

        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(CourseSchedule.objects.count(), 1)
        course = Course.objects.get()
        schedule = CourseSchedule.objects.get()
        self.assertEqual(course.fullname, "Test Calendar Course")
        self.assertEqual(course.price, 325)
        self.assertIn("2026-01-19 to 2026-01-23", schedule.notes)
        self.assertIn("Technical Courses!D4", schedule.notes)

    @patch("apps.courses.management.commands.seed_calendar_2026.MoodleClient")
    def test_seed_reuses_matching_moodle_course(self, client_class):
        client = client_class.return_value
        client.get_courses.return_value = [{
            "id": 44,
            "shortname": "CAL26-TEST-123456",
            "fullname": "Test Calendar Course",
            "categoryid": 1,
            "categoryname": "Miscellaneous",
        }]

        self.run_command()

        self.assertEqual(Course.objects.get().moodle_course_id, 44)
        client.create_course.assert_not_called()

    @patch("apps.courses.management.commands.seed_calendar_2026.MoodleClient")
    def test_seed_creates_missing_moodle_course(self, client_class):
        client = client_class.return_value
        client.get_courses.return_value = []
        client.create_course.return_value = {
            "id": 45,
            "shortname": "CAL26-TEST-123456",
        }

        self.run_command("--moodle-category-id", "7")

        self.assertEqual(Course.objects.get().moodle_course_id, 45)
        client.create_course.assert_called_once_with(
            shortname="CAL26-TEST-123456",
            fullname="Test Calendar Course",
            category_id=7,
            summary="A test course.",
            visible=True,
        )

    def test_bundled_calendar_contains_the_reviewed_course_catalogue(self):
        from apps.courses.management.commands.seed_calendar_2026 import Command

        payload = Command().load_data()

        self.assertEqual(payload["version"], 1)
        self.assertGreaterEqual(len(payload["courses"]), 160)
        self.assertTrue(any(
            course["fullname"] == "33KV Switching Fundamentals"
            for course in payload["courses"]
        ))
        self.assertTrue(any(course["schedules"] for course in payload["courses"]))
