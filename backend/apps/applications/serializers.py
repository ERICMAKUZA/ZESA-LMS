from rest_framework import serializers

from centres.models import Centre
from .models import Application, ApplicationDocument, ApplicationStatus, ApplicationStatusHistory


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = ("id", "filename", "file", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationStatusHistory
        fields = ("id", "from_status", "to_status", "changed_by", "changed_by_name", "notes", "changed_at")
        read_only_fields = ("id", "changed_at")

    def get_changed_by_name(self, obj):
        return obj.changed_by.full_name if obj.changed_by else "System"


class ApplicationCreateSerializer(serializers.ModelSerializer):
    applicant = serializers.HiddenField(default=serializers.CurrentUserDefault())
    preferred_centre = serializers.PrimaryKeyRelatedField(
        queryset=Centre.objects.all(), allow_null=True, required=False,
    )
    line_manager_email = serializers.EmailField(required=False, allow_blank=True, default='')

    class Meta:
        model = Application
        fields = (
            "id", "applicant", "course", "motivation",
            "line_manager_email", "department", "employee_id",
            "hexco_level", "student_category",
            "preferred_centre",
            "is_resident", "hostel_name", "room_number",
            "guardian_name", "guardian_contact", "guardian_email",
            "responsible_party",
            "national_id_doc", "academic_certs_doc", "student_photo",
        )
        read_only_fields = ("id",)

    def validate_course(self, course):
        if not course.is_active:
            raise serializers.ValidationError("This course is not currently active.")
        if not course.requires_approval:
            raise serializers.ValidationError("This course does not require an application.")
        return course

    def validate(self, attrs):
        # course may be absent on partial updates
        course = attrs.get("course")
        if course is None:
            return attrs
        applicant = attrs["applicant"]
        conflict = (
            Application.objects.filter(applicant=applicant, course=course)
            .exclude(status=ApplicationStatus.REJECTED)
        )
        if self.instance:
            conflict = conflict.exclude(pk=self.instance.pk)
        if conflict.exists():
            raise serializers.ValidationError(
                "You already have an active application for this course."
            )
        return attrs

    def create(self, validated_data):
        applicant = validated_data["applicant"]
        if not validated_data.get("employee_id") and applicant.employee_id:
            validated_data["employee_id"] = applicant.employee_id
        if not validated_data.get("department") and applicant.department:
            validated_data["department"] = applicant.department
        return super().create(validated_data)


class ApplicationListSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    course_name = serializers.CharField(source="course.fullname", read_only=True)

    class Meta:
        model = Application
        fields = (
            "id", "applicant_name", "applicant_email",
            "course_name", "status", "source",
            "escalated", "escalated_at",
            "submitted_at", "created_at",
        )

    def get_applicant_name(self, obj):
        return obj.applicant.full_name


class ApplicationDetailSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    course_name = serializers.CharField(source="course.fullname", read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    assigned_centre = serializers.PrimaryKeyRelatedField(
        queryset=Centre.objects.all(), allow_null=True, required=False,
    )
    assigned_centre_name = serializers.CharField(
        source="assigned_centre.name", read_only=True, default=None,
    )
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    recent_history = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    enrollment = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            "id", "applicant", "applicant_name", "applicant_email",
            "course", "course_name", "status",
            "motivation", "line_manager_email", "department", "employee_id",
            "hexco_level",
            "national_id_doc", "academic_certs_doc", "student_photo",
            "assigned_centre", "assigned_centre_name",
            "reviewer", "reviewer_name", "reviewer_notes",
            "rejection_reason", "more_info_request",
            "code_of_conduct_signed", "code_of_conduct_signed_at",
            "escalated", "escalated_at",
            "submitted_at", "reviewed_at", "approved_at", "enrolled_at",
            "created_at", "updated_at",
            "documents", "recent_history",
            "payment", "enrollment",
        )
        read_only_fields = (
            "id", "applicant", "status", "reviewer",
            "created_at", "updated_at",
        )

    def get_applicant_name(self, obj):
        return obj.applicant.full_name

    def get_reviewer_name(self, obj):
        return obj.reviewer.full_name if obj.reviewer else None

    def get_recent_history(self, obj):
        entries = obj.history.order_by("-changed_at")[:5]
        return ApplicationStatusHistorySerializer(entries, many=True).data

    def get_payment(self, obj):
        try:
            p = obj.payment
            return {
                "id": str(p.id),
                "amount": str(p.amount),
                "currency": p.currency,
                "status": p.status,
                "method": p.method,
                "confirmed_at": p.confirmed_at,
            }
        except Exception:
            return None

    def get_enrollment(self, obj):
        try:
            e = obj.enrollment
            return {
                "id": str(e.id),
                "status": e.status,
                "enrolled_at": e.enrolled_at,
                "moodle_course_url": e.moodle_course_url,
            }
        except Exception:
            return None


class ReviewActionSerializer(serializers.Serializer):
    ACTION_APPROVE = "approve"
    ACTION_REJECT = "reject"
    ACTION_MORE_INFO = "request_more_info"

    ACTION_CHOICES = [
        (ACTION_APPROVE, "Approve"),
        (ACTION_REJECT, "Reject"),
        (ACTION_MORE_INFO, "Request More Info"),
    ]

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    rejection_reason = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["action"] == self.ACTION_REJECT and not attrs.get("rejection_reason"):
            raise serializers.ValidationError(
                {"rejection_reason": "A rejection reason is required."}
            )
        if attrs["action"] == self.ACTION_MORE_INFO and not attrs.get("notes"):
            raise serializers.ValidationError(
                {"notes": "Notes are required when requesting more information."}
            )
        return attrs
