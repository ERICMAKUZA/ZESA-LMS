from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.conf import settings
from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.applications.models import Application, ApplicationStatus
from apps.certificates.models import Certificate
from apps.courses.models import Course, CourseSchedule, CourseType
from apps.enrollments.models import Enrollment

from .models import Notification
from .services import queue_acceptance_notification, queue_certificate_collection_notification
from .tasks import broadcast_upcoming_courses, send_notification


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class LifecycleNotificationTests(TestCase):
    def setUp(self):
        today = patch("apps.workflows.services.timezone.localdate", return_value=date(2026, 9, 14))
        today.start()
        self.addCleanup(today.stop)
        self.student = User.objects.create_user(
            email="student@example.com", password="SafePass123!",
            first_name="Test", last_name="Student",
        )
        self.reviewer = User.objects.create_user(
            email="reviewer@example.com", password="SafePass123!",
            first_name="Test", last_name="Reviewer", role=User.Role.REVIEWER,
        )
        self.course = Course.objects.create(
            moodle_course_id=8123, shortname="SAFETY", fullname="Electrical Safety",
            price=Decimal("125.00"), duration_days=5,
        )
        self.schedule = CourseSchedule.objects.create(
            course=self.course, year=2026, month=11, week_in_month=2,
            payment_due_date=date(2026, 11, 5),
        )
        self.application = Application.objects.create(
            applicant=self.student, course=self.course,
            motivation="Training", line_manager_email="manager@example.com",
            department="ELECTRICAL", status=ApplicationStatus.UNDER_REVIEW,
            reviewer=self.reviewer,
        )

    def test_acceptance_renders_exact_bank_terms_due_date_and_bell_record(self):
        notification = queue_acceptance_notification(self.application)

        self.assertEqual(Notification.objects.filter(application=self.application).count(), 1)
        self.assertEqual(notification.recipient, self.student)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.action_url, f"/applications/{self.application.id}")
        self.assertEqual(notification.subject, "Acceptance: Electrical Safety")
        self.assertEqual(
            notification.message,
            "You have been accepted for Electrical Safety, commencing on 9 November 2026. "
            "You are required to pay full course fees of USD 125.00 by 5 November 2026. "
            "Banking details: Bank: STANBIC, Park Lane Branch. "
            "Account Name: ZESA National Training Centre. "
            "Account Number: 9140000940908 (Nostro). Upload proof of payment.",
        )

    def test_acceptance_defaults_due_date_to_intake_start(self):
        self.schedule.payment_due_date = None
        self.schedule.save(update_fields=["payment_due_date"])

        notification = queue_acceptance_notification(self.application)

        self.assertIn("commencing on 9 November 2026", notification.message)
        self.assertIn("by 9 November 2026", notification.message)

    def test_acceptance_without_intake_or_fee_does_not_invent_details(self):
        self.schedule.delete()
        self.course.price = None
        self.course.save(update_fields=["price"])

        notification = queue_acceptance_notification(self.application)

        self.assertIn("commencing on to be announced", notification.message)
        self.assertIn("USD to be confirmed by to be announced", notification.message)
        self.assertIn("9140000940908", notification.message)

    def test_certificate_collection_renders_exact_hours(self):
        enrollment = Enrollment.objects.create(
            application=self.application, moodle_course_id=self.course.moodle_course_id,
        )
        certificate = Certificate.objects.create(
            enrollment=enrollment, user=self.student, course=self.course,
            certificate_number="ZNTC-TEST-1",
        )

        notification = queue_certificate_collection_notification(certificate)

        self.assertEqual(notification.recipient, self.student)
        self.assertEqual(notification.application, self.application)
        self.assertEqual(notification.action_url, "/certificates")
        self.assertEqual(
            notification.message,
            "Your certificates for Electrical Safety are ready for collection. "
            "Collection time 0830-1600hrs Monday to Friday.",
        )

    def test_issuing_certificate_queues_collection_before_pdf_generation(self):
        self.application.status = ApplicationStatus.ENROLLED
        self.application.save(update_fields=["status"])
        enrollment = Enrollment.objects.create(
            application=self.application, moodle_course_id=self.course.moodle_course_id,
        )

        with patch.object(Certificate, "generate_number", return_value="ZNTC-TEST-2"), patch(
            "apps.certificates.tasks.generate_certificate_pdf.delay"
        ):
            certificate = Certificate.issue_from_enrollment(enrollment, issued_by=self.reviewer)

        notification = Notification.objects.get(application=self.application)
        self.assertEqual(notification.recipient, self.student)
        self.assertIn("ready for collection", notification.message)
        self.assertEqual(certificate.user, self.student)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationStatus.CERTIFIED)
        self.assertTrue(
            self.application.history.filter(
                from_status=ApplicationStatus.ENROLLED,
                to_status=ApplicationStatus.CERTIFIED,
            ).exists()
        )

    def test_notification_dispatch_uses_same_bell_record_for_email(self):
        with patch("apps.workflows.services.send_notification.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                notification = queue_acceptance_notification(self.application)
        delay.assert_called_once_with(notification.id)

        send_notification.apply(args=[notification.id]).get()

        notification.refresh_from_db()
        self.assertTrue(notification.is_sent)
        self.assertIsNotNone(notification.sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].body, notification.message)
        self.assertEqual(mail.outbox[0].to, [self.student.email])

    def test_queue_failure_is_recorded_on_the_bell_item(self):
        with patch("apps.workflows.services.send_notification.delay", side_effect=RuntimeError("broker offline")):
            with self.captureOnCommitCallbacks(execute=True):
                notification = queue_acceptance_notification(self.application)

        notification.refresh_from_db()
        self.assertFalse(notification.is_sent)
        self.assertEqual(notification.error_message, "Could not enqueue email: broker offline")

    def test_zero_email_deliveries_are_not_marked_sent(self):
        notification = queue_acceptance_notification(self.application)

        with patch("apps.workflows.tasks.send_mail", return_value=0), patch.object(
            send_notification, "retry", side_effect=RuntimeError("retry queued")
        ):
            with self.assertRaisesRegex(RuntimeError, "retry queued"):
                send_notification.run(notification.id)

        notification.refresh_from_db()
        self.assertFalse(notification.is_sent)
        self.assertIsNone(notification.sent_at)
        self.assertIn("zero recipients", notification.error_message)


class QuarterlyBroadcastTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com", password="SafePass123!",
            first_name="Test", last_name="Student",
        )
        self.inactive = User.objects.create_user(
            email="inactive@example.com", password="SafePass123!",
            first_name="Inactive", last_name="Student", is_active=False,
        )
        self.hexco = CourseType.objects.create(code="HEXCO", name="HEXCO")
        self.uz = CourseType.objects.create(code="UZ", name="UZ")
        self.other = CourseType.objects.create(code="OTHER", name="Other")

    def add_intake(self, name, course_type, month, *, active=True):
        course = Course.objects.create(
            moodle_course_id=9000 + Course.objects.count(), shortname=name,
            fullname=name, course_type=course_type, is_active=active,
        )
        CourseSchedule.objects.create(
            course=course, year=2026, month=month, week_in_month=1,
        )

    @override_settings(PORTAL_BASE_URL="https://training.example.com")
    def test_broadcast_lists_only_next_quarter_hexco_uz_and_is_idempotent(self):
        self.add_intake("Electrical Engineering", self.hexco, 10)
        self.add_intake("Business Studies", self.uz, 12)
        self.add_intake("Not Q4", self.hexco, 9)
        self.add_intake("Other Type", self.other, 11)
        self.add_intake("Inactive Course", self.uz, 11, active=False)

        first = broadcast_upcoming_courses("2026-Q4")
        second = broadcast_upcoming_courses("2026-Q4")

        self.assertEqual(first, 1)
        self.assertEqual(second, 0)
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.recipient, self.student)
        self.assertEqual(notification.subject, "Upcoming courses ALERT 2026-Q4")
        self.assertIn("Electrical Engineering", notification.message)
        self.assertIn("Business Studies", notification.message)
        self.assertIn("5 October 2026", notification.message)
        self.assertIn("7 December 2026", notification.message)
        self.assertNotIn("Not Q4", notification.message)
        self.assertNotIn("Other Type", notification.message)
        self.assertNotIn("Inactive Course", notification.message)
        self.assertIn("https://training.example.com/courses/", notification.message)
        self.assertEqual(notification.action_url, "/courses")

    def test_empty_quarter_does_not_create_a_notification(self):
        self.assertEqual(broadcast_upcoming_courses("2026-Q4"), 0)
        self.assertFalse(Notification.objects.exists())

    def test_beat_runs_one_month_before_each_quarter(self):
        schedule = settings.CELERY_BEAT_SCHEDULE["broadcast-upcoming-courses"]
        self.assertEqual(schedule["task"], "workflows.broadcast_upcoming_courses")
        self.assertEqual(schedule["schedule"].month_of_year, {3, 6, 9, 12})
        self.assertEqual(schedule["schedule"].day_of_month, {1})
