from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application, ApplicationStatus
from apps.courses.models import Course, CourseCategory, CourseSchedule
from apps.enrollments.models import Enrollment
from apps.enrollments.tasks import _notify_lecturer_enrolled


class CourseManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="Password123!",
            first_name="Course",
            last_name="Admin",
            role=User.Role.ADMIN,
        )
        self.lecturer_one = User.objects.create_user(
            email="lecturer.one@example.com",
            password="Password123!",
            first_name="Tariro",
            last_name="Moyo",
            role=User.Role.LECTURER,
        )
        self.lecturer_two = User.objects.create_user(
            email="lecturer.two@example.com",
            password="Password123!",
            first_name="Tendai",
            last_name="Ncube",
            role=User.Role.LECTURER,
        )
        self.category = CourseCategory.objects.create(name="Electrical", moodle_id=11)
        self.client.force_authenticate(self.admin)

    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_admin_can_create_course_with_multiple_lecturers(self, create_course):
        create_course.return_value = {"id": 501}

        response = self.client.post(
            "/api/courses/admin/",
            {
                "moodle_course_id": 501,
                "shortname": "ELEC-101",
                "fullname": "Electrical Safety Fundamentals",
                "summary": "A foundation course for electrical safety.",
                "category_id": self.category.id,
                "duration_days": 5,
                "level": "BEGINNER",
                "price": "120.00",
                "max_capacity": 24,
                "is_active": True,
                "requires_approval": True,
                "lecturer_ids": [self.lecturer_one.id, self.lecturer_two.id],
                "initial_schedule": {
                    "year": 2026,
                    "month": 9,
                    "week_in_month": 1,
                    "max_capacity": 24,
                    "notes": "First intake.",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("lecturers", response.data)
        self.assertEqual(
            {lecturer["id"] for lecturer in response.data["lecturers"]},
            {self.lecturer_one.id, self.lecturer_two.id},
        )
        self.assertEqual(response.data["upcoming_schedules"][0]["max_capacity"], 24)

    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_admin_course_creation_creates_the_matching_moodle_course(self, create_course):
        create_course.return_value = {"id": 505}

        response = self.client.post(
            "/api/courses/admin/",
            {
                "shortname": "ELEC-105",
                "fullname": "Electrical Networks",
                "summary": "Planning and operating electrical networks.",
                "category_id": self.category.id,
                "duration_days": 10,
                "level": "INTERMEDIATE",
                "price": "250.00",
                "max_capacity": 16,
                "is_active": True,
                "requires_approval": True,
                "lecturer_ids": [self.lecturer_one.id],
                "initial_schedule": {
                    "year": 2026,
                    "month": 10,
                    "week_in_month": 2,
                    "max_capacity": 16,
                    "notes": "Network operations intake.",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["moodle_course_id"], 505)
        create_course.assert_called_once_with(
            shortname="ELEC-105",
            fullname="Electrical Networks",
            category_id=self.category.moodle_id,
            summary="Planning and operating electrical networks.",
            visible=True,
        )

    def test_new_course_requires_an_initial_intake(self):
        response = self.client.post(
            "/api/courses/admin/",
            {
                "shortname": "ELEC-105A",
                "fullname": "Electrical Networks Planning",
                "category_id": self.category.id,
                "lecturer_ids": [self.lecturer_one.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("initial_schedule", response.data)

    @patch("apps.courses.services.MoodleClient.update_course", create=True)
    def test_admin_course_update_updates_the_matching_moodle_course(self, update_course):
        course = Course.objects.create(
            moodle_course_id=506,
            shortname="ELEC-106",
            fullname="Electrical Networks",
            summary="Original summary.",
            category=self.category,
            duration_days=10,
        )
        course.lecturers.add(self.lecturer_one)

        response = self.client.patch(
            f"/api/courses/admin/{course.id}/",
            {
                "fullname": "Electrical Networks Advanced",
                "summary": "Updated network operations content.",
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        update_course.assert_called_once_with(
            course_id=506,
            shortname="ELEC-106",
            fullname="Electrical Networks Advanced",
            category_id=self.category.moodle_id,
            summary="Updated network operations content.",
            visible=False,
        )

    def test_course_update_cannot_remove_every_lecturer(self):
        course = Course.objects.create(
            moodle_course_id=508,
            shortname="ELEC-108",
            fullname="Electrical Reliability",
            category=self.category,
        )
        course.lecturers.add(self.lecturer_one)

        response = self.client.patch(
            f"/api/courses/admin/{course.id}/",
            {"lecturer_ids": []},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lecturer_ids", response.data)

    def test_assigned_lecturer_can_see_every_intake_for_their_course(self):
        course = Course.objects.create(
            moodle_course_id=502,
            shortname="ELEC-102",
            fullname="Switchgear Safety",
            category=self.category,
            duration_days=3,
        )
        course.lecturers.add(self.lecturer_one)
        schedule = CourseSchedule.objects.create(
            course=course,
            year=2026,
            month=9,
            week_in_month=2,
            max_capacity=20,
        )

        self.client.force_authenticate(self.lecturer_one)
        response = self.client.get("/api/courses/lecturer/schedules/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [str(schedule.id)])

    def test_legacy_schedule_lecturer_retains_intake_access(self):
        course = Course.objects.create(
            moodle_course_id=510,
            shortname="ELEC-110",
            fullname="Electrical Inspection",
            category=self.category,
            duration_days=3,
        )
        schedule = CourseSchedule.objects.create(
            course=course,
            year=2026,
            month=11,
            week_in_month=1,
            max_capacity=20,
            lecturer=self.lecturer_one,
        )

        self.client.force_authenticate(self.lecturer_one)
        response = self.client.get("/api/courses/lecturer/schedules/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [str(schedule.id)])

    def test_public_course_response_does_not_expose_lecturer_contact_details(self):
        course = Course.objects.create(
            moodle_course_id=507,
            shortname="ELEC-107",
            fullname="Electrical Safety Awareness",
            category=self.category,
        )
        course.lecturers.add(self.lecturer_one)

        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/courses/{course.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lecturers"], [])

    def test_lecturer_detail_response_excludes_sensitive_application_data(self):
        course = Course.objects.create(
            moodle_course_id=509,
            shortname="ELEC-109",
            fullname="Electrical Commissioning",
            category=self.category,
            duration_days=5,
        )
        course.lecturers.add(self.lecturer_one)
        student = User.objects.create_user(
            email="student.three@example.com",
            password="Password123!",
            first_name="Tatenda",
            last_name="Moyo",
            role=User.Role.STUDENT,
        )
        application = Application.objects.create(
            applicant=student,
            course=course,
            status=ApplicationStatus.ENROLLED,
            motivation="I want to improve my commissioning skills.",
            line_manager_email="manager@example.com",
            department="Electrical",
            guardian_name="Private guardian",
        )

        self.client.force_authenticate(self.lecturer_one)
        response = self.client.get(f"/api/lecturer/applications/{application.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("guardian_name", response.data)
        self.assertNotIn("national_id_doc", response.data)

    def test_admin_can_load_all_active_lecturers_for_course_assignment(self):
        for number in range(25):
            User.objects.create_user(
                email=f"lecturer.{number + 10}@example.com",
                password="Password123!",
                first_name="Lecturer",
                last_name=str(number + 10),
                role=User.Role.LECTURER,
            )

        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/admin/lecturers/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 27)

    @patch("apps.courses.services.MoodleClient.delete_course", create=True)
    @patch("apps.courses.views.CourseSerializer.save", side_effect=RuntimeError("Database write failed"))
    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_failed_portal_save_cleans_up_the_new_moodle_course(self, create_course, serializer_save, delete_course):
        create_course.return_value = {"id": 511}

        response = self.client.post(
            "/api/courses/admin/",
            {
                "shortname": "ELEC-111",
                "fullname": "Electrical Fault Finding",
                "category_id": self.category.id,
                "duration_days": 5,
                "lecturer_ids": [self.lecturer_one.id],
                "initial_schedule": {
                    "year": 2026,
                    "month": 12,
                    "week_in_month": 1,
                    "max_capacity": 12,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        delete_course.assert_called_once_with(511)

    def test_assigned_lecturer_can_see_students_for_their_course(self):
        course = Course.objects.create(
            moodle_course_id=503,
            shortname="ELEC-103",
            fullname="Electrical Protection",
            category=self.category,
            duration_days=5,
        )
        course.lecturers.add(self.lecturer_one)
        student = User.objects.create_user(
            email="student@example.com",
            password="Password123!",
            first_name="Nyasha",
            last_name="Dube",
            role=User.Role.STUDENT,
        )
        application = Application.objects.create(
            applicant=student,
            course=course,
            status=ApplicationStatus.ENROLLED,
            motivation="I want to improve my electrical protection skills.",
            line_manager_email="manager@example.com",
            department="Electrical",
        )

        self.client.force_authenticate(self.lecturer_one)
        response = self.client.get("/api/lecturer/applications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data["results"]], [str(application.id)])

    @patch("apps.workflows.services.queue_notification")
    def test_every_assigned_lecturer_is_notified_when_a_student_enrols(self, queue_notification):
        course = Course.objects.create(
            moodle_course_id=504,
            shortname="ELEC-104",
            fullname="Electrical Maintenance",
            category=self.category,
            duration_days=5,
        )
        course.lecturers.add(self.lecturer_one, self.lecturer_two)
        schedule = CourseSchedule.objects.create(
            course=course,
            year=2026,
            month=10,
            week_in_month=1,
            max_capacity=20,
        )
        student = User.objects.create_user(
            email="student.two@example.com",
            password="Password123!",
            first_name="Rudo",
            last_name="Dube",
            role=User.Role.STUDENT,
        )
        application = Application.objects.create(
            applicant=student,
            course=course,
            status=ApplicationStatus.ENROLLED,
            motivation="I want to improve my maintenance skills.",
            line_manager_email="manager@example.com",
            department="Electrical",
        )
        enrollment = Enrollment.objects.create(
            application=application,
            moodle_course_id=course.moodle_course_id,
            schedule=schedule,
            status="ENROLLED",
        )

        _notify_lecturer_enrolled(enrollment)

        self.assertEqual(queue_notification.call_count, 2)
        self.assertEqual(
            {call.kwargs["recipient"] for call in queue_notification.call_args_list},
            {self.lecturer_one, self.lecturer_two},
        )
