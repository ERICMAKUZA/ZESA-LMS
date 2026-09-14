from django.test import TestCase

from apps.accounts.models import User
from apps.applications.models import (
    Application,
    ApplicationAcademicResult,
    ApplicationAcademicSitting,
)
from apps.applications.services.qualification import assess_application, shortlist_ordering
from apps.courses.models import (
    Course,
    CourseCategory,
    CourseType,
    GradeBand,
    QualificationProfile,
    QualificationRequirement,
)


class QualificationAssessmentTests(TestCase):
    def setUp(self):
        self.category = CourseCategory.objects.create(name="Engineering", moodle_id=91)
        self.course_type = CourseType.objects.create(
            code="HEXCO",
            name="HEXCO",
            requires_qualification_assessment=True,
        )
        self.grade_a = GradeBand.objects.create(code="TEST_A", label="A", rank=6, points=5)
        self.grade_b = GradeBand.objects.create(code="TEST_B", label="B", rank=5, points=4)
        self.grade_c = GradeBand.objects.create(code="TEST_C", label="C", rank=4, points=3)
        self.profile = QualificationProfile.objects.create(
            code="TEST_HEXCO",
            name="Test HEXCO profile",
            course_type=self.course_type,
            max_o_level_sittings=2,
            minimum_total_points=10,
            prefer_a_level_sciences=True,
        )
        QualificationRequirement.objects.create(
            profile=self.profile,
            education_level="O_LEVEL",
            subject_group=["Mathematics"],
            minimum_grade_band=self.grade_b,
        )
        QualificationRequirement.objects.create(
            profile=self.profile,
            education_level="O_LEVEL",
            subject_group=["English"],
            minimum_grade_band=self.grade_c,
        )
        self.course = Course.objects.create(
            moodle_course_id=901,
            shortname="HEXCO-TEST",
            fullname="HEXCO Test Course",
            category=self.category,
            course_type=self.course_type,
            qualification_profile=self.profile,
            minimum_points_required=10,
            duration_days=5,
        )

    def application(self, email):
        user = User.objects.create_user(
            email=email,
            password="Password123!",
            first_name="Test",
            last_name=email.split("@")[0].title(),
            role=User.Role.STUDENT,
        )
        return Application.objects.create(
            applicant=user,
            course=self.course,
            motivation="I would like to learn.",
            line_manager_email="manager@example.com",
            department="ELECTRICAL",
        )

    def add_result(self, application, subject, grade_band, sitting_number=1, education_level="O_LEVEL"):
        sitting, _ = ApplicationAcademicSitting.objects.get_or_create(
            application=application,
            education_level=education_level,
            sitting_number=sitting_number,
            defaults={"exam_year": 2025, "exam_session": "NOVEMBER"},
        )
        return ApplicationAcademicResult.objects.create(
            sitting=sitting,
            subject=subject,
            grade_band=grade_band,
        )

    def test_assessment_requires_maths_b_or_better_and_minimum_points(self):
        application = self.application("maths.failure@example.com")
        self.add_result(application, "Mathematics", self.grade_c)
        self.add_result(application, "English", self.grade_b)
        self.add_result(application, "Physics", self.grade_b)

        assessment = assess_application(application)

        self.assertFalse(assessment.qualifies)
        self.assertIn("REQUIRED_SUBJECT:MATHEMATICS", assessment.failed_rule_codes)
        self.assertEqual(assessment.assessment_summary, "Does not fully meet requirements")

    def test_assessment_uses_best_o_level_grade_once_per_subject(self):
        application = self.application("best.grade@example.com")
        self.add_result(application, "Mathematics", self.grade_b, sitting_number=1)
        self.add_result(application, "Mathematics", self.grade_a, sitting_number=2)
        self.add_result(application, "English", self.grade_b)
        self.add_result(application, "Physics", self.grade_b)

        assessment = assess_application(application)

        self.assertTrue(assessment.qualifies)
        self.assertEqual(assessment.total_o_level_points, 13)

    def test_shortlist_prefers_a_level_sciences_then_points_then_name(self):
        science = self.application("zulu@example.com")
        points = self.application("alpha@example.com")
        lower = self.application("beta@example.com")
        for application, maths_grade in ((science, self.grade_a), (points, self.grade_a), (lower, self.grade_b)):
            self.add_result(application, "Mathematics", maths_grade)
            self.add_result(application, "English", self.grade_b)
            self.add_result(application, "Physics", self.grade_b)
        self.add_result(science, "Physics", self.grade_b, education_level="A_LEVEL")
        for application in (science, points, lower):
            assess_application(application)

        ranked = list(shortlist_ordering(Application.objects.filter(course=self.course)))

        self.assertEqual([item.applicant.last_name for item in ranked], ["Zulu", "Alpha", "Beta"])
