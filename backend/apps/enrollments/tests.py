from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.utils import timezone

from apps.accounts.models import User
from apps.applications.models import Application, ApplicationStatus
from apps.courses.models import Course, CourseSchedule
from apps.workflows.models import Notification

from .models import Enrollment, EnrollmentAttendanceResponse, EnrollmentStatus


class AttendanceResponseTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com", password="Password123!",
            first_name="Student", last_name="One",
        )
        self.other_student = User.objects.create_user(
            email="other@example.com", password="Password123!",
            first_name="Student", last_name="Two",
        )
        self.course = Course.objects.create(
            moodle_course_id=501, shortname="SAFE-101",
            fullname="Safety Training", duration_days=5,
        )
        self.current = CourseSchedule.objects.create(
            course=self.course, year=2026, month=9, week_in_month=1,
            max_capacity=2, enrolled_count=1,
        )
        self.next_schedule = CourseSchedule.objects.create(
            course=self.course, year=2026, month=10, week_in_month=1,
            max_capacity=1, enrolled_count=0,
        )
        self.application = Application.objects.create(
            applicant=self.student, course=self.course, motivation="Training",
            line_manager_email="manager@example.com", department="ELECTRICAL",
        )
        self.enrollment = Enrollment.objects.create(
            application=self.application, moodle_course_id=501,
            status=EnrollmentStatus.ENROLLED, schedule=self.current,
            start_date=self.current.get_approximate_start_date(),
            end_date=self.current.get_approximate_end_date(),
        )
        self.url = f"/api/enrollments/{self.enrollment.id}/attendance-response/"
        self.client.force_authenticate(self.student)

    def test_confirm_records_response_without_moving_capacity(self):
        response = self.client.post(self.url, {"response": "CONFIRMED"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["response"], "CONFIRMED")
        self.assertEqual(response.data["target_schedule"], None)
        self.assertTrue(EnrollmentAttendanceResponse.objects.filter(
            enrollment=self.enrollment, response="CONFIRMED",
        ).exists())
        self.enrollment.refresh_from_db()
        self.current.refresh_from_db()
        self.assertEqual(self.enrollment.schedule, self.current)
        self.assertEqual(self.current.enrolled_count, 1)

    def test_defer_moves_to_next_open_intake_and_updates_both_counters(self):
        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["response"], "DEFERRED")
        self.enrollment.refresh_from_db()
        self.current.refresh_from_db()
        self.next_schedule.refresh_from_db()
        self.assertEqual(self.enrollment.schedule, self.next_schedule)
        self.assertEqual(self.enrollment.start_date, self.next_schedule.get_approximate_start_date())
        self.assertEqual(self.enrollment.end_date, self.next_schedule.get_approximate_end_date())
        self.assertEqual(self.current.enrolled_count, 0)
        self.assertEqual(self.next_schedule.enrolled_count, 1)
        self.assertEqual(
            self.enrollment.attendance_response.target_schedule, self.next_schedule,
        )

    def test_defer_preserves_remaining_students_when_source_counter_is_stale(self):
        other_application = Application.objects.create(
            applicant=self.other_student, course=self.course, motivation="Training",
        )
        Enrollment.objects.create(
            application=other_application, moodle_course_id=501,
            status=EnrollmentStatus.ENROLLED, schedule=self.current,
        )

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.current.refresh_from_db()
        self.assertEqual(self.current.enrolled_count, 1)

    def test_defer_clears_stale_source_reservation(self):
        self.current.enrolled_count = 2
        self.current.save(update_fields=["enrolled_count"])

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.current.refresh_from_db()
        self.assertEqual(self.current.enrolled_count, 0)

    def test_full_next_intake_stays_pending_for_staff(self):
        self.next_schedule.enrolled_count = 1
        self.next_schedule.save(update_fields=["enrolled_count"])

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["response"], "PENDING_STAFF")
        self.assertIsNone(response.data["target_schedule"])
        self.enrollment.refresh_from_db()
        self.current.refresh_from_db()
        self.assertEqual(self.enrollment.schedule, self.current)
        self.assertEqual(self.current.enrolled_count, 1)

    def test_no_next_intake_stays_pending_for_staff(self):
        self.next_schedule.delete()

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["response"], "PENDING_STAFF")
        self.assertIsNone(response.data["target_schedule"])

    def test_does_not_pick_another_course_or_earlier_intake(self):
        self.next_schedule.delete()
        other_course = Course.objects.create(
            moodle_course_id=502, shortname="OTHER", fullname="Other Course",
        )
        CourseSchedule.objects.create(
            course=other_course, year=2026, month=11, week_in_month=1,
        )
        CourseSchedule.objects.create(
            course=self.course, year=2026, month=8, week_in_month=1,
        )

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.data["response"], "PENDING_STAFF")

    def test_duplicate_response_does_not_move_twice(self):
        self.client.post(self.url, {"response": "DEFER"}, format="json")
        duplicate = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)
        self.next_schedule.refresh_from_db()
        self.assertEqual(self.next_schedule.enrolled_count, 1)
        self.assertEqual(EnrollmentAttendanceResponse.objects.count(), 1)

    def test_other_student_cannot_respond(self):
        self.client.force_authenticate(self.other_student)

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(EnrollmentAttendanceResponse.objects.exists())

    def test_invalid_response_does_not_write(self):
        response = self.client.post(self.url, {"response": "MAYBE"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EnrollmentAttendanceResponse.objects.exists())

    def test_non_object_payload_is_rejected(self):
        response = self.client.post(self.url, ["DEFER"], format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EnrollmentAttendanceResponse.objects.exists())

    def test_unenrolled_student_cannot_respond(self):
        self.enrollment.status = EnrollmentStatus.UNENROLLED
        self.enrollment.save(update_fields=["status"])

        response = self.client.post(self.url, {"response": "CONFIRMED"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EnrollmentAttendanceResponse.objects.exists())

    def test_defer_does_not_underflow_stale_source_counter(self):
        self.current.enrolled_count = 0
        self.current.save(update_fields=["enrolled_count"])

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.current.refresh_from_db()
        self.assertEqual(self.current.enrolled_count, 0)

    def test_stale_target_counter_cannot_overfill_an_intake(self):
        other_application = Application.objects.create(
            applicant=self.other_student, course=self.course, motivation="Training",
            line_manager_email="manager@example.com", department="ELECTRICAL",
        )
        Enrollment.objects.create(
            application=other_application, moodle_course_id=501,
            status=EnrollmentStatus.ENROLLED, schedule=self.next_schedule,
        )

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.data["response"], "PENDING_STAFF")
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.schedule, self.current)

    def test_outcome_creates_a_student_notification(self):
        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification = Notification.objects.get(recipient=self.student)
        self.assertIn(self.course.fullname, notification.message)
        self.assertEqual(notification.action_url, "/dashboard/learning")

    def test_student_list_exposes_saved_response_state(self):
        self.client.post(self.url, {"response": "CONFIRMED"}, format="json")

        response = self.client.get("/api/enrollments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["attendance_response"]["response"], "CONFIRMED")
        self.assertEqual(response.data[0]["id"], str(self.enrollment.id))

    def test_defer_skips_full_intake_for_later_open_space(self):
        self.next_schedule.enrolled_count = 1
        self.next_schedule.save(update_fields=["enrolled_count"])
        later = CourseSchedule.objects.create(
            course=self.course, year=2026, month=11, week_in_month=1,
            max_capacity=2, enrolled_count=0,
        )

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.data["response"], "DEFERRED")
        self.enrollment.refresh_from_db()
        later.refresh_from_db()
        self.assertEqual(self.enrollment.schedule, later)
        self.assertEqual(later.enrolled_count, 1)

    def test_no_assigned_intake_stays_pending_for_staff(self):
        self.enrollment.schedule = None
        self.enrollment.save(update_fields=["schedule"])

        response = self.client.post(self.url, {"response": "DEFER"}, format="json")

        self.assertEqual(response.data["response"], "PENDING_STAFF")
        self.assertIsNone(response.data["target_schedule"])

    def test_unauthenticated_response_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url, {"response": "CONFIRMED"}, format="json")

        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertFalse(EnrollmentAttendanceResponse.objects.exists())


class InitialIntakeReservationTests(APITestCase):
    def setUp(self):
        student = User.objects.create_user(
            email="reservation@example.com", password="Password123!",
            first_name="Reservation", last_name="Student",
        )
        student.student_id = "TEST-RESERVATION-001"
        student.save(update_fields=["student_id"])
        self.course = Course.objects.create(
            moodle_course_id=601, shortname="RESERVE-101", fullname="Reservation Training",
            duration_days=5,
        )
        year = timezone.localdate().year + 1
        self.first = CourseSchedule.objects.create(
            course=self.course, year=year, month=1, week_in_month=1,
            max_capacity=1, enrolled_count=1,
        )
        self.second = CourseSchedule.objects.create(
            course=self.course, year=year, month=2, week_in_month=1,
            max_capacity=2, enrolled_count=0,
        )
        self.application = Application.objects.create(
            applicant=student, course=self.course, motivation="Training",
            status=ApplicationStatus.PAYMENT_CONFIRMED, code_of_conduct_signed=True,
        )

    @patch("apps.enrollments.tasks.sync_to_moodle.delay")
    def test_enroll_skips_full_intake_and_reserves_next(self, _delay):
        self.application.enroll()

        enrollment = Enrollment.objects.get(application=self.application)
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual(enrollment.schedule, self.second)
        self.assertEqual(self.first.enrolled_count, 1)
        self.assertEqual(self.second.enrolled_count, 1)
        self.assertEqual(enrollment.start_date, self.second.get_approximate_start_date())

    @patch("apps.enrollments.tasks.sync_to_moodle.delay")
    def test_full_intakes_do_not_mark_application_enrolled(self, _delay):
        self.second.enrolled_count = self.second.max_capacity
        self.second.save(update_fields=["enrolled_count"])

        with self.assertRaisesRegex(ValueError, "No open intake"):
            self.application.enroll()

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationStatus.PAYMENT_CONFIRMED)
        self.assertFalse(Enrollment.objects.filter(application=self.application).exists())
