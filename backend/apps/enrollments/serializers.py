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
        )
        read_only_fields = fields

    def get_moodle_course_url(self, obj):
        if not obj.moodle_course_id:
            return None
        base = getattr(settings, "MOODLE_BASE_URL", "").rstrip("/")
        return f"{base}/course/view.php?id={obj.moodle_course_id}"


class EnrollmentListSerializer(serializers.ModelSerializer):
    applicant_email = serializers.EmailField(
        source="application.applicant.email", read_only=True
    )
    applicant_name = serializers.SerializerMethodField()
    course_name = serializers.CharField(
        source="application.course.fullname", read_only=True
    )

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "applicant_email",
            "applicant_name",
            "course_name",
            "status",
            "enrolled_at",
        )

    def get_applicant_name(self, obj):
        return obj.application.applicant.full_name
