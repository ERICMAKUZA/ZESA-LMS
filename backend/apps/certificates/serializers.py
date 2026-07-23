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


class CertificatePublicSerializer(serializers.ModelSerializer):
    """
    Safe public representation for certificate verification — served with
    no auth to anyone scanning the QR code or checking a serial by hand,
    so it exposes only what's printed on the certificate itself, nothing
    account-internal (email, ids, etc).
    """
    valid = serializers.SerializerMethodField()
    holder_name = serializers.CharField(source="user.full_name", read_only=True)
    student_id = serializers.CharField(source="student_id_snapshot", read_only=True)
    course = serializers.CharField(source="course.fullname", read_only=True)
    course_shortname = serializers.CharField(source="course.shortname", read_only=True)
    centre_name = serializers.SerializerMethodField()
    level_display = serializers.CharField(source="get_programme_level_display", read_only=True)
    status = serializers.CharField(source="status_display", read_only=True)
    issue_date = serializers.DateField(format="%d %B %Y", read_only=True)
    revoked_at = serializers.DateTimeField(format="%d %B %Y %H:%M", read_only=True)
    verification_url = serializers.CharField(read_only=True)

    class Meta:
        model = Certificate
        fields = (
            "certificate_number", "valid", "holder_name", "student_id",
            "course", "course_shortname", "centre_name",
            "level_display", "issue_date", "issued_at", "status",
            "is_revoked", "revoked_at", "revocation_reason",
            "verification_url",
        )

    def get_valid(self, obj):
        return not obj.is_revoked

    def get_centre_name(self, obj):
        return obj.centre.name if obj.centre else "ZNTC Harare"
