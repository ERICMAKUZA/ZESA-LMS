from datetime import date

from django.test import override_settings
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application, ApplicationStatus
from apps.courses.models import AcademicCalendarEvent, Course, CourseSchedule
from apps.enrollments.models import Enrollment, EnrollmentStatus
from apps.workflows.models import Notification


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CalendarEventApiTests(APITestCase):
    url = "/api/courses/calendar-events/"

    def setUp(self):
        self.trainer = User.objects.create_user(
            email="trainer@example.com", password="SafePass123!",
            first_name="Test", last_name="Trainer", role=User.Role.TRAINER,
        )
        self.student = User.objects.create_user(
            email="student@example.com", password="SafePass123!",
            first_name="Test", last_name="Student",
        )
        self.lecturer = User.objects.create_user(
            email="lecturer@example.com", password="SafePass123!",
            first_name="Test", last_name="Lecturer", role=User.Role.LECTURER,
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com", password="SafePass123!",
            first_name="Other", last_name="Student",
        )
        self.course = Course.objects.create(
            moodle_course_id=7331, shortname="ELEC", fullname="Electrical Safety", duration_days=5,
        )
        self.course.lecturers.add(self.lecturer)
        self.schedule = CourseSchedule.objects.create(
            course=self.course, year=2026, month=11, week_in_month=1,
        )
        application = Application.objects.create(
            applicant=self.student, course=self.course, status=ApplicationStatus.ENROLLED,
            motivation="Training", line_manager_email="manager@example.com",
            department="ELECTRICAL",
        )
        Enrollment.objects.create(
            application=application, schedule=self.schedule,
            moodle_course_id=self.course.moodle_course_id, status=EnrollmentStatus.ENROLLED,
        )
        self.payload = {
            "event_type": "EXAMINATION", "title": "Final examinations",
            "course": self.course.id, "schedule": str(self.schedule.id),
            "start_date": "2026-11-02", "end_date": "2026-11-06",
            "timetable_url": "https://example.com/exam-timetable.pdf",
        }

    def test_publish_requires_training_role_and_timetable(self):
        self.client.force_authenticate(self.student)
        denied = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(AcademicCalendarEvent.objects.count(), 0)

        self.client.force_authenticate(self.trainer)
        invalid = self.client.post(self.url, {**self.payload, "timetable_url": ""}, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("timetable_url", invalid.data)
        self.assertEqual(Notification.objects.count(), 0)

    def test_publish_exam_sends_scoped_email_and_bell_with_timetable(self):
        self.client.force_authenticate(self.trainer)
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 201)
        event = AcademicCalendarEvent.objects.get()
        self.assertEqual(event.published_by, self.trainer)
        self.assertEqual(event.audience, AcademicCalendarEvent.Audience.BOTH)
        self.assertEqual(event.start_date, date(2026, 11, 2))
        self.assertEqual(
            set(Notification.objects.values_list("recipient_id", flat=True)),
            {self.student.id, self.lecturer.id},
        )
        self.assertEqual(Notification.objects.count(), 2)
        self.assertFalse(Notification.objects.get(recipient=self.student).is_read)
        for notification in Notification.objects.all():
            self.assertIn("2 November 2026", notification.message)
            self.assertIn("6 November 2026", notification.message)
            self.assertIn("exam-timetable.pdf", notification.message)
            self.assertEqual(notification.action_url, self.payload["timetable_url"])

    def test_marks_deadline_uses_distinct_student_and_lecturer_wording(self):
        self.client.force_authenticate(self.trainer)
        response = self.client.post(self.url, {
            "event_type": "MARKS_DEADLINE", "title": "Coursework marks",
            "course": self.course.id, "start_date": "2026-11-20",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Notification.objects.get(recipient=self.student).message,
            "Kindly verify your coursework marks by 20 November 2026.",
        )
        self.assertEqual(
            Notification.objects.get(recipient=self.lecturer).message,
            "Deadline for submission of marks: 20 November 2026.",
        )
        self.assertFalse(Notification.objects.filter(recipient=self.outsider).exists())

    def test_exam_fee_is_student_only_and_other_event_dates_are_validated(self):
        self.client.force_authenticate(self.trainer)
        invalid = self.client.post(self.url, {
            "event_type": "SEMESTER_BREAK", "title": "Break",
            "start_date": "2026-12-10", "end_date": "2026-12-01",
        }, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("end_date", invalid.data)

        response = self.client.post(self.url, {
            "event_type": "EXAM_FEE", "title": "Exam fee notice",
            "course": self.course.id, "start_date": "2026-11-01",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertIn("current examination-fee schedule", Notification.objects.get().message)

    def test_ranged_event_types_include_run_dates_and_fee_reminders(self):
        self.client.force_authenticate(self.trainer)
        for event_type in (
            "SEMESTER_START", "SEMESTER_END", "BLOCK_START", "BLOCK_END", "SEMESTER_BREAK",
        ):
            with self.subTest(event_type=event_type):
                Notification.objects.all().delete()
                response = self.client.post(self.url, {
                    "event_type": event_type, "title": "November session",
                    "course": self.course.id,
                    "start_date": "2026-11-02", "end_date": "2026-11-06",
                }, format="json")
                self.assertEqual(response.status_code, 201)
                message = Notification.objects.get(recipient=self.student).message
                self.assertIn("2 November 2026", message)
                self.assertIn("6 November 2026", message)
                if event_type != "SEMESTER_BREAK":
                    self.assertIn("settle all outstanding course fees", message)

    def test_schedule_must_belong_to_selected_course(self):
        other_course = Course.objects.create(
            moodle_course_id=7332, shortname="OTHER", fullname="Other Course",
        )
        self.client.force_authenticate(self.trainer)
        response = self.client.post(self.url, {
            **self.payload, "course": other_course.id,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("schedule", response.data)
        self.assertEqual(Notification.objects.count(), 0)

    def test_commencement_bell_opens_attendance_response_page(self):
        enrollment = Enrollment.objects.get(application__applicant=self.student)
        enrollment.status = EnrollmentStatus.PENDING
        enrollment.save(update_fields=["status"])
        self.client.force_authenticate(self.trainer)
        response = self.client.post(self.url, {
            "event_type": "COMMENCEMENT", "title": "Course commencement",
            "course": self.course.id, "schedule": str(self.schedule.id),
            "start_date": "2026-11-02",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get(recipient=self.student)
        self.assertEqual(notification.action_url, "/dashboard/learning")
        self.assertEqual(
            notification.message,
            "The Electrical Safety course will commence on 2 November 2026. "
            "Kindly confirm attendance.",
        )

    def test_commencement_requires_explicit_course_and_schedule(self):
        self.client.force_authenticate(self.trainer)
        payload = {
            "event_type": "COMMENCEMENT", "title": "Course commencement",
            "start_date": "2026-11-02",
        }
        missing_course = self.client.post(
            self.url, {**payload, "schedule": str(self.schedule.id)}, format="json"
        )
        missing_schedule = self.client.post(
            self.url, {**payload, "course": self.course.id}, format="json"
        )

        self.assertEqual(missing_course.status_code, 400)
        self.assertIn("course", missing_course.data)
        self.assertEqual(missing_schedule.status_code, 400)
        self.assertIn("schedule", missing_schedule.data)
        self.assertFalse(AcademicCalendarEvent.objects.exists())

    def test_calendar_options_exposes_frontend_event_and_audience_choices(self):
        self.client.force_authenticate(self.trainer)
        response = self.client.options(self.url)

        self.assertEqual(response.status_code, 200)
        actions = response.data["actions"]["POST"]
        self.assertEqual(
            {item["value"] for item in actions["event_type"]["choices"]},
            {
                "COMMENCEMENT", "EXAMINATION", "SEMESTER_START", "SEMESTER_END",
                "BLOCK_START", "BLOCK_END", "SEMESTER_BREAK", "EXAM_FEE", "MARKS_DEADLINE",
                "DEFERMENT",
            },
        )
        self.assertEqual(
            {item["value"] for item in actions["audience"]["choices"]},
            {"STUDENTS", "LECTURERS", "BOTH"},
        )

    def test_deferment_notifies_only_course_students_with_tba(self):
        self.client.force_authenticate(self.trainer)
        response = self.client.post(self.url, {
            "event_type": "DEFERMENT", "title": "Course postponed",
            "course": self.course.id, "start_date": "2026-11-02",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get(recipient=self.student)
        self.assertEqual(notification.action_url, f"/courses/{self.course.id}")
        self.assertEqual(
            notification.message,
            "Please be advised Electrical Safety course which was scheduled to commence "
            "on 2 November 2026 has been postponed to TBA.",
        )
        self.assertFalse(Notification.objects.filter(recipient=self.outsider).exists())

    def test_deferment_requires_course_and_later_new_date(self):
        self.client.force_authenticate(self.trainer)
        payload = {
            "event_type": "DEFERMENT", "title": "Course postponed",
            "start_date": "2026-11-02", "end_date": "2026-11-09",
        }
        missing_course = self.client.post(self.url, payload, format="json")
        self.assertEqual(missing_course.status_code, 400)
        self.assertIn("course", missing_course.data)

        invalid = self.client.post(self.url, {
            **payload, "course": self.course.id, "end_date": "2026-11-02",
        }, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("end_date", invalid.data)

        valid = self.client.post(self.url, {
            **payload, "course": self.course.id,
        }, format="json")
        self.assertEqual(valid.status_code, 201)
        self.assertIn("postponed to 9 November 2026", Notification.objects.get().message)
