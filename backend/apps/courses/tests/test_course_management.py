from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application, ApplicationStatus
from apps.courses.models import (
    CertificationType,
    Course,
    CourseCategory,
    CourseSchedule,
    CourseType,
    Department,
    GradeBand,
    QualificationProfile,
    QualificationRequirement,
)
from apps.enrollments.models import Enrollment
from apps.enrollments.tasks import _notify_lecturer_enrolled
from apps.courses.serializers import CourseScheduleSerializer


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
        self.trainer = User.objects.create_user(
            email="trainer@example.com",
            password="Password123!",
            first_name="Training",
            last_name="Manager",
            role=User.Role.TRAINER,
        )
        self.category = CourseCategory.objects.create(name="Electrical", moodle_id=11)
        self.course_type = CourseType.objects.create(code="STANDARD", name="Standard")
        self.client.force_authenticate(self.admin)

    def test_course_catalogue_is_public(self):
        course = Course.objects.create(
            moodle_course_id=81001,
            shortname="PUBLIC-COURSE",
            fullname="Public Course",
            category=self.category,
        )
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/courses/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(course.id, [item["id"] for item in response.data["results"]])

    def test_trainer_can_create_training_taxonomy(self):
        self.client.force_authenticate(self.trainer)

        department = self.client.post(
            "/api/courses/training/departments/",
            {"code": "ELEC", "name": "Electrical", "description": "Electrical training."},
            format="json",
        )
        course_type = self.client.post(
            "/api/courses/training/course-types/",
            {"code": "HEXCO", "name": "HEXCO", "description": "National qualifications."},
            format="json",
        )
        certification = self.client.post(
            "/api/courses/training/certification-types/",
            {
                "course_type": course_type.data["id"],
                "code": "NC",
                "name": "National Certificate",
            },
            format="json",
        )

        self.assertEqual(department.status_code, status.HTTP_201_CREATED)
        self.assertEqual(course_type.status_code, status.HTTP_201_CREATED)
        self.assertEqual(certification.status_code, status.HTTP_201_CREATED)
        self.assertEqual(certification.data["course_type"], course_type.data["id"])

    def test_lecturer_cannot_change_shared_training_taxonomy(self):
        self.client.force_authenticate(self.lecturer_one)

        response = self.client.post(
            "/api/courses/training/course-types/",
            {"code": "SHORT", "name": "Short Course"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_new_course_uses_active_default_qualification_profile(self, create_course):
        create_course.return_value = {"id": 8871}
        self.course_type.requires_qualification_assessment = True
        profile = QualificationProfile.objects.create(
            code="DEFAULT_STANDARD", name="Default Standard", course_type=self.course_type,
        )
        self.course_type.default_qualification_profile = profile
        self.course_type.save(update_fields=[
            "requires_qualification_assessment", "default_qualification_profile",
        ])

        response = self.client.post("/api/courses/admin/", {
            "shortname": "DEFAULT-101", "fullname": "Default Profile Course",
            "category_id": self.category.id, "course_type_id": self.course_type.id,
            "duration_days": 5, "lecturer_ids": [self.lecturer_one.id],
            "initial_schedule": {
                "year": 2026, "month": 11, "week_in_month": 1, "max_capacity": 20,
            },
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        course = Course.objects.get(moodle_course_id=8871)
        self.assertEqual(course.qualification_profile, profile)
        self.assertEqual(response.data["qualification_profile"]["id"], profile.id)

    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_standard_course_can_enable_qualification_assessment_independently(self, create_course):
        create_course.return_value = {"id": 8890}
        profile = QualificationProfile.objects.create(
            code="COURSE_OPT_IN", name="Course opt-in profile", course_type=self.course_type,
        )

        response = self.client.post("/api/courses/admin/", {
            "shortname": "OPT-IN-101", "fullname": "Opt-in course",
            "category_id": self.category.id, "course_type_id": self.course_type.id,
            "duration_days": 5, "lecturer_ids": [self.lecturer_one.id],
            "qualification_assessment_enabled": True,
            "qualification_profile_id": profile.id,
            "initial_schedule": {
                "year": 2026, "month": 11, "week_in_month": 1, "max_capacity": 20,
            },
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        course = Course.objects.get(moodle_course_id=8890)
        self.assertTrue(course.uses_qualification_assessment)
        self.assertTrue(response.data["qualification_assessment_enabled"])

    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_initial_schedule_saves_payment_due_date(self, create_course):
        create_course.return_value = {"id": 8872}
        response = self.client.post("/api/courses/admin/", {
            "shortname": "DUE-101", "fullname": "Payment Due Course",
            "category_id": self.category.id, "course_type_id": self.course_type.id,
            "duration_days": 5, "lecturer_ids": [self.lecturer_one.id],
            "initial_schedule": {
                "year": 2026, "month": 11, "week_in_month": 1, "max_capacity": 20,
                "payment_due_date": "2026-11-01",
            },
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schedule = Course.objects.get(moodle_course_id=8872).schedules.get()
        self.assertEqual(schedule.payment_due_date.isoformat(), "2026-11-01")
        self.assertEqual(CourseScheduleSerializer(schedule).data["payment_due_date"], "2026-11-01")

    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_initial_schedule_rejects_payment_due_after_start(self, create_course):
        create_course.return_value = {"id": 8873}
        response = self.client.post("/api/courses/admin/", {
            "shortname": "DUE-102", "fullname": "Invalid Payment Due Course",
            "category_id": self.category.id, "course_type_id": self.course_type.id,
            "duration_days": 5, "lecturer_ids": [self.lecturer_one.id],
            "initial_schedule": {
                "year": 2026, "month": 11, "week_in_month": 1, "max_capacity": 20,
                "payment_due_date": "2026-11-03",
            },
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_due_date", response.data["initial_schedule"])
        create_course.assert_not_called()

    def test_schedule_serializer_rejects_due_date_after_start(self):
        course = Course.objects.create(
            moodle_course_id=8874, shortname="DUE-103", fullname="Schedule Due Course",
        )
        schedule = CourseSchedule.objects.create(
            course=course, year=2026, month=11, week_in_month=1,
        )
        serializer = CourseScheduleSerializer(
            schedule, data={"payment_due_date": "2026-11-03"}, partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("payment_due_date", serializer.errors)

    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_trainer_can_list_lecturers_and_create_a_course(self, create_course):
        create_course.return_value = {"id": 512}
        self.client.force_authenticate(self.trainer)

        lecturer_list = self.client.get("/api/admin/lecturers/")
        response = self.client.post(
            "/api/courses/admin/",
            {
                "shortname": "ELEC-112",
                "fullname": "Trainer Created Course",
                "category_id": self.category.id,
                "course_type_id": self.course_type.id,
                "duration_days": 3,
                "lecturer_ids": [self.lecturer_one.id],
                "initial_schedule": {
                    "year": 2026,
                    "month": 11,
                    "week_in_month": 1,
                    "max_capacity": 20,
                },
            },
            format="json",
        )

        self.assertEqual(lecturer_list.status_code, status.HTTP_200_OK)
        self.assertIn(self.lecturer_one.id, [item["id"] for item in lecturer_list.data])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["lecturers"][0]["id"], self.lecturer_one.id)

    def test_certification_type_requires_an_active_course_type(self):
        self.course_type.is_active = False
        self.course_type.save(update_fields=["is_active"])

        response = self.client.post(
            "/api/courses/training/certification-types/",
            {
                "course_type": self.course_type.id,
                "code": "NC",
                "name": "National Certificate",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("course_type", response.data)

    def test_trainer_can_configure_grade_bands_and_qualification_requirements(self):
        self.client.force_authenticate(self.trainer)
        course_type = CourseType.objects.create(
            code="HEXCO",
            name="HEXCO",
            requires_qualification_assessment=True,
        )
        grade_band = self.client.post(
            "/api/courses/training/grade-bands/",
            {"code": "B_PLUS", "label": "B+", "rank": 7, "points": 5},
            format="json",
        )
        self.assertEqual(grade_band.status_code, status.HTTP_201_CREATED, grade_band.data)
        profile = self.client.post(
            "/api/courses/training/qualification-profiles/",
            {
                "code": "HEXCO_DEFAULT",
                "name": "HEXCO default",
                "course_type": course_type.id,
                "max_o_level_sittings": 2,
                "minimum_total_points": 12,
                "prefer_a_level_sciences": True,
            },
            format="json",
        )
        self.assertEqual(profile.status_code, status.HTTP_201_CREATED, profile.data)
        requirement = self.client.post(
            "/api/courses/training/qualification-requirements/",
            {
                "profile": profile.data["id"],
                "education_level": "O_LEVEL",
                "subject_group": ["Mathematics"],
                "minimum_grade_band": grade_band.data["id"],
                "is_required": True,
            },
            format="json",
        )

        self.assertEqual(requirement.status_code, status.HTTP_201_CREATED)
        self.assertEqual(requirement.data["minimum_grade_band"], grade_band.data["id"])
        self.assertEqual(QualificationRequirement.objects.count(), 1)

    def test_course_requires_profile_when_its_type_requires_qualification_assessment(self):
        self.course_type.requires_qualification_assessment = True
        self.course_type.save(update_fields=["requires_qualification_assessment"])

        response = self.client.post(
            "/api/courses/admin/",
            {
                "shortname": "ELEC-QUAL",
                "fullname": "Qualification Required Course",
                "category_id": self.category.id,
                "course_type_id": self.course_type.id,
                "lecturer_ids": [self.lecturer_one.id],
                "initial_schedule": {
                    "year": 2026,
                    "month": 11,
                    "week_in_month": 1,
                    "max_capacity": 20,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("qualification_profile_id", response.data)

    def test_training_configuration_cannot_be_deleted(self):
        response = self.client.delete(
            f"/api/courses/training/course-types/{self.course_type.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(CourseType.objects.filter(id=self.course_type.id).exists())

    def test_deactivated_training_configuration_remains_visible_to_managers(self):
        department = Department.objects.create(code="TELE", name="Telecommunications")

        response = self.client.patch(
            f"/api/courses/training/departments/{department.id}/",
            {"is_active": False},
            format="json",
        )
        listing = self.client.get("/api/courses/training/departments/?include_inactive=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            {"id": department.id, "is_active": False},
            [
                {"id": item["id"], "is_active": item["is_active"]}
                for item in listing.data["results"]
            ],
        )

    @patch("apps.courses.services.MoodleClient.create_course", create=True)
    def test_course_rejects_certification_from_another_course_type(self, create_course):
        hexco = CourseType.objects.create(code="HEXCO", name="HEXCO")
        invalid_certificate = CertificationType.objects.create(
            course_type=self.course_type,
            code="STD",
            name="Standard Certificate",
        )

        response = self.client.post(
            "/api/courses/admin/",
            {
                "shortname": "ELEC-102",
                "fullname": "Electrical Safety",
                "category_id": self.category.id,
                "course_type_id": hexco.id,
                "certification_type_ids": [invalid_certificate.id],
                "lecturer_ids": [self.lecturer_one.id],
                "initial_schedule": {
                    "year": 2026,
                    "month": 10,
                    "week_in_month": 1,
                    "max_capacity": 20,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("certification_type_ids", response.data)
        create_course.assert_not_called()

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
                "course_type_id": self.course_type.id,
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
                "course_type_id": self.course_type.id,
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
                "course_type_id": self.course_type.id,
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

    @patch("apps.courses.services.MoodleClient.update_course", create=True)
    def test_course_can_retain_an_inactive_configured_type(self, update_course):
        course = Course.objects.create(
            moodle_course_id=507,
            shortname="ELEC-107",
            fullname="Electrical Maintenance",
            category=self.category,
            course_type=self.course_type,
        )
        course.lecturers.add(self.lecturer_one)
        self.course_type.is_active = False
        self.course_type.save(update_fields=["is_active"])

        response = self.client.patch(
            f"/api/courses/admin/{course.id}/",
            {
                "summary": "Existing course with a retired classification.",
                "course_type_id": self.course_type.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["course_type"]["id"], self.course_type.id)

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
                "course_type_id": self.course_type.id,
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
