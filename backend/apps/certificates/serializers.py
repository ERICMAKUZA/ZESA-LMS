from rest_framework import serializers

from apps.courses.serializers import CourseSummarySerializer

from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    course_detail = CourseSummarySerializer(source="course", read_only=True)
    pdf_url = serializers.SerializerMethodField()
    status = serializers.CharField(source="status_display", read_only=True)

    class Meta:
        model = Certificate
        fields = (
            "id", "enrollment", "user", "user_name", "course", "course_detail",
            "certificate_number", "pdf_url", "issued_at", "issued_by",
            "is_revoked", "status",
        )
        read_only_fields = ("id", "certificate_number", "issued_at")

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
        return obj.pdf_url
