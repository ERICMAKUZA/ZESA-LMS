from rest_framework import serializers

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

    class Meta:
        model = Application
        fields = (
            "applicant", "course", "motivation",
            "line_manager_email", "department", "employee_id",
        )

    def validate_course(self, course):
        if not course.is_active:
            raise serializers.ValidationError("This course is not currently active.")
        if not course.requires_approval:
            raise serializers.ValidationError("This course does not require an application.")
        return course

    def validate(self, attrs):
        applicant = attrs["applicant"]
        course = attrs["course"]
        conflict = (
            Application.objects.filter(applicant=applicant, course=course)
            .exclude(status=ApplicationStatus.REJECTED)
        )
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
            "course_name", "status", "submitted_at", "created_at",
        )

    def get_applicant_name(self, obj):
        return obj.applicant.full_name


class ApplicationDetailSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    course_name = serializers.CharField(source="course.fullname", read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    recent_history = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            "id", "applicant", "applicant_name", "applicant_email",
            "course", "course_name", "status",
            "motivation", "line_manager_email", "department", "employee_id",
            "reviewer", "reviewer_name", "reviewer_notes",
            "rejection_reason", "more_info_request",
            "submitted_at", "reviewed_at", "approved_at", "enrolled_at",
            "created_at", "updated_at",
            "documents", "recent_history",
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
