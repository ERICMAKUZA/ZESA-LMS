from rest_framework import serializers

from apps.courses.serializers import CourseSummarySerializer

from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    course_detail = CourseSummarySerializer(source="course", read_only=True)

    class Meta:
        model = Certificate
        fields = (
            "id", "enrollment", "user", "user_name", "course", "course_detail",
            "certificate_number", "pdf_url", "issued_at",
        )
        read_only_fields = ("id", "certificate_number", "issued_at")
