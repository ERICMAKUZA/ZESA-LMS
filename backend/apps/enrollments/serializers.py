from django.conf import settings
from rest_framework import serializers

from .models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    applicant_email = serializers.EmailField(
        source="application.applicant.email", read_only=True
    )
    applicant_name = serializers.SerializerMethodField()
    course_name = serializers.CharField(
        source="application.course.fullname", read_only=True
    )
    moodle_course_url = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "application",
            "applicant_email",
            "applicant_name",
            "course_name",
            "moodle_user_id",
            "moodle_course_id",
            "status",
            "enrolled_at",
            "unenrolled_at",
            "completion_status",
            "last_access",
            "error_message",
            "created_at",
            "moodle_course_url",
            "start_date",
            "end_date",
            "is_suspended",
            "suspension_reason",
        )
        read_only_fields = fields

    def get_applicant_name(self, obj):
        return obj.application.applicant.full_name

    def get_moodle_course_url(self, obj):
        if not obj.moodle_course_id:
            return None
        base = getattr(settings, "MOODLE_BASE_URL", "").rstrip("/")
        return f"{base}/course/view.php?id={obj.moodle_course_id}"


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(
        source="application.course.fullname", read_only=True
    )
    moodle_course_url = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = (
            "id", "application", "course_name",
            "moodle_user_id", "moodle_course_url",
            "status", "enrolled_at",
            "start_date", "end_date", "is_suspended",
        )
        read_only_fields = fields

    def get_moodle_course_url(self, obj):
        if not obj.moodle_course_id:
            return None
        base = getattr(settings, "MOODLE_BASE_URL", "").rstrip("/")
        return f"{base}/course/view.php?id={obj.moodle_course_id}"


class EnrollmentListSerializer(serializers.ModelSerializer):
    ref = serializers.CharField(source="application.ref", read_only=True)
    applicant_email = serializers.EmailField(
        source="application.applicant.email", read_only=True
    )
    applicant_name = serializers.SerializerMethodField()
    student_id = serializers.CharField(
        source="application.applicant.student_id", read_only=True
    )
    zntc_email = serializers.CharField(
        source="application.applicant.zntc_email", read_only=True
    )
    course_name = serializers.CharField(
        source="application.course.fullname", read_only=True
    )
    assigned_centre_name = serializers.CharField(
        source="application.assigned_centre.name", read_only=True, default=None,
    )
    department = serializers.CharField(source="application.department", read_only=True)
    hexco_level = serializers.CharField(source="application.hexco_level", read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "ref",
            "applicant_email",
            "applicant_name",
            "student_id",
            "zntc_email",
            "course_name",
            "assigned_centre_name",
            "department",
            "hexco_level",
            "status",
            "error_message",
            "enrolled_at",
            "start_date",
            "end_date",
            "is_suspended",
        )

    def get_applicant_name(self, obj):
        return obj.application.applicant.full_name
