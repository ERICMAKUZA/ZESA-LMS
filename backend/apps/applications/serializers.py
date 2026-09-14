from django.db import transaction
from rest_framework import serializers

from centres.models import Centre
from apps.courses.models import CertificationType, Department, GradeBand

from .models import (
    Application,
    ApplicationAcademicResult,
    ApplicationAcademicSitting,
    ApplicationDocument,
    ApplicationQualificationAssessment,
    ApplicationQualificationOverride,
    ApplicationStatus,
    ApplicationStatusHistory,
)
from .services.qualification import assess_application


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = ("id", "filename", "file", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationStatusHistory
        fields = (
            "id", "from_status", "to_status", "changed_by", "changed_by_name",
            "changed_by_ec_number", "notes", "changed_at",
        )
        read_only_fields = ("id", "changed_at")

    def get_changed_by_name(self, obj):
        # changed_by_name_snapshot is authoritative (survives the actor's
        # account being edited/deactivated); fall back for pre-snapshot rows.
        return obj.changed_by_name_snapshot or (obj.changed_by.full_name if obj.changed_by else "System")


class AcademicResultInputSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=150)
    grade_band_id = serializers.PrimaryKeyRelatedField(
        queryset=GradeBand.objects.filter(is_active=True), source="grade_band"
    )


class AcademicSittingInputSerializer(serializers.Serializer):
    education_level = serializers.ChoiceField(choices=ApplicationAcademicSitting.EDUCATION_LEVEL_CHOICES)
    sitting_number = serializers.IntegerField(min_value=1)
    exam_year = serializers.IntegerField(min_value=1950, max_value=2100)
    exam_session = serializers.CharField(required=False, allow_blank=True, default="")
    results = AcademicResultInputSerializer(many=True, min_length=1)


class ApplicationAcademicResultSerializer(serializers.ModelSerializer):
    grade_band_id = serializers.IntegerField(source="grade_band_id", read_only=True)

    class Meta:
        model = ApplicationAcademicResult
        fields = ("id", "subject", "grade_band_id", "grade_label_snapshot", "points_snapshot", "rank_snapshot")


class ApplicationAcademicSittingSerializer(serializers.ModelSerializer):
    results = ApplicationAcademicResultSerializer(many=True, read_only=True)

    class Meta:
        model = ApplicationAcademicSitting
        fields = ("id", "education_level", "sitting_number", "exam_year", "exam_session", "results")


class ApplicationQualificationAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationQualificationAssessment
        fields = (
            "qualifies", "total_o_level_points", "has_a_level_sciences",
            "failed_rule_codes", "assessment_summary", "configuration_snapshot", "assessed_at",
        )


class ApplicationQualificationOverrideSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.full_name", read_only=True)

    class Meta:
        model = ApplicationQualificationOverride
        fields = ("id", "reviewer", "reviewer_name", "note", "created_at")
        read_only_fields = ("id", "reviewer", "reviewer_name", "created_at")


class ApplicationCreateSerializer(serializers.ModelSerializer):
    applicant = serializers.HiddenField(default=serializers.CurrentUserDefault())
    preferred_centre = serializers.PrimaryKeyRelatedField(
        queryset=Centre.objects.all(), allow_null=True, required=False,
    )
    line_manager_email = serializers.EmailField(required=False, allow_blank=True, default='')
    department = serializers.CharField(required=False, allow_blank=True, default='')
    selected_department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="selected_department", required=False, allow_null=True,
    )
    certification_type_id = serializers.PrimaryKeyRelatedField(
        queryset=CertificationType.objects.all(), source="certification_type", required=False, allow_null=True,
    )
    academic_sittings = AcademicSittingInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Application
        fields = (
            "id", "applicant", "course", "motivation",
            "line_manager_email", "department", "employee_id",
            "hexco_level", "selected_department_id", "certification_type_id", "academic_sittings",
            "student_category",
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
        # Course may be absent on a partial update; its configured rules still apply.
        course = attrs.get("course") or (self.instance.course if self.instance else None)
        if course is None:
            return attrs
        # applicant is a HiddenField, so on a partial update where it isn't
        # in the payload DRF skips it entirely rather than applying its
        # CurrentUserDefault — fall back to the existing instance's owner.
        applicant = attrs.get("applicant") or (self.instance.applicant if self.instance else None)
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

        selected_department = attrs.get("selected_department") if "selected_department" in attrs else getattr(
            self.instance, "selected_department", None
        )
        course_departments = list(course.departments.filter(is_active=True))
        if len(course_departments) == 1 and selected_department is None:
            selected_department = course_departments[0]
            attrs["selected_department"] = selected_department
        elif len(course_departments) > 1 and selected_department is None:
            raise serializers.ValidationError(
                {"selected_department_id": "Select one of the departments linked to this course."}
            )
        if selected_department:
            if not selected_department.is_active:
                raise serializers.ValidationError({"selected_department_id": "Select an active department."})
            if course_departments and selected_department.id not in {item.id for item in course_departments}:
                raise serializers.ValidationError(
                    {"selected_department_id": "The selected department is not linked to this course."}
                )

        certification_type = attrs.get("certification_type") if "certification_type" in attrs else getattr(
            self.instance, "certification_type", None
        )
        course_certifications = list(course.certification_types.filter(is_active=True))
        if len(course_certifications) == 1 and certification_type is None:
            certification_type = course_certifications[0]
            attrs["certification_type"] = certification_type
        elif course_certifications and certification_type is None:
            raise serializers.ValidationError(
                {"certification_type_id": "Select a certification type for this course."}
            )
        if certification_type:
            if not certification_type.is_active or certification_type not in course_certifications:
                raise serializers.ValidationError(
                    {"certification_type_id": "The selected certification type is not available for this course."}
                )

        sittings = attrs.get("academic_sittings")
        profile = course.qualification_profile or getattr(course.course_type, "default_qualification_profile", None)
        if sittings is not None and profile:
            o_level_sittings = [item for item in sittings if item["education_level"] == "O_LEVEL"]
            sitting_keys = {(item["education_level"], item["sitting_number"]) for item in sittings}
            if len(sitting_keys) != len(sittings):
                raise serializers.ValidationError({"academic_sittings": "Each education level and sitting number must be unique."})
            if len(o_level_sittings) > profile.max_o_level_sittings:
                raise serializers.ValidationError(
                    {"academic_sittings": f"This course allows at most {profile.max_o_level_sittings} O-Level sittings."}
                )
        return attrs

    def _replace_academic_sittings(self, application, sittings):
        application.academic_sittings.all().delete()
        for sitting_data in sittings:
            result_data = sitting_data.pop("results")
            sitting = ApplicationAcademicSitting.objects.create(application=application, **sitting_data)
            ApplicationAcademicResult.objects.bulk_create([
                ApplicationAcademicResult(
                    sitting=sitting,
                    subject=result["subject"],
                    grade_band=result["grade_band"],
                    grade_label_snapshot=result["grade_band"].label,
                    points_snapshot=result["grade_band"].points,
                    rank_snapshot=result["grade_band"].rank,
                )
                for result in result_data
            ])

    def create(self, validated_data):
        sittings = validated_data.pop("academic_sittings", None)
        applicant = validated_data["applicant"]
        if not validated_data.get("employee_id") and applicant.employee_id:
            validated_data["employee_id"] = applicant.employee_id
        if not validated_data.get("department") and applicant.department:
            validated_data["department"] = applicant.department
        with transaction.atomic():
            application = super().create(validated_data)
            application.sync_legacy_training_fields()
            application.save(update_fields=["department", "hexco_level", "updated_at"])
            if sittings is not None:
                self._replace_academic_sittings(application, sittings)
            assess_application(application)
        return application

    def update(self, instance, validated_data):
        sittings = validated_data.pop("academic_sittings", None)
        with transaction.atomic():
            application = super().update(instance, validated_data)
            application.sync_legacy_training_fields()
            application.save(update_fields=["department", "hexco_level", "updated_at"])
            if sittings is not None:
                self._replace_academic_sittings(application, sittings)
            assess_application(application)
        return application


class ApplicationListSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    course_name = serializers.CharField(source="course.fullname", read_only=True)
    enrollment_status = serializers.SerializerMethodField()
    qualification_assessment = ApplicationQualificationAssessmentSerializer(read_only=True)

    class Meta:
        model = Application
        fields = (
            "id", "applicant_name", "applicant_email",
            "course_name", "status", "source",
            "escalated", "escalated_at",
            "submitted_at", "created_at",
            "enrollment_status",
            "qualification_assessment",
        )

    def get_applicant_name(self, obj):
        return obj.applicant.full_name

    def get_enrollment_status(self, obj):
        try:
            return obj.enrollment.status
        except Exception:
            return None


class LecturerApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    student_id = serializers.CharField(source="applicant.student_id", read_only=True)
    course_name = serializers.CharField(source="course.fullname", read_only=True)
    assigned_centre_name = serializers.CharField(
        source="assigned_centre.name", read_only=True, default=None,
    )
    lecturer_signed_off_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            "id", "ref", "applicant_name", "student_id",
            "course_name", "assigned_centre_name", "status",
            "enrolled_at",
            "lecturer_signed_off", "lecturer_signed_off_at",
            "lecturer_signed_off_by_name", "lecturer_signoff_notes",
        )

    def get_applicant_name(self, obj):
        return obj.applicant.full_name

    def get_lecturer_signed_off_by_name(self, obj):
        return obj.lecturer_signed_off_by.full_name if obj.lecturer_signed_off_by else None


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
    certificate = serializers.SerializerMethodField()
    lecturer_signed_off_by_name = serializers.SerializerMethodField()
    academic_sittings = ApplicationAcademicSittingSerializer(many=True, read_only=True)
    qualification_assessment = ApplicationQualificationAssessmentSerializer(read_only=True)
    qualification_overrides = ApplicationQualificationOverrideSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = (
            "id", "applicant", "applicant_name", "applicant_email",
            "course", "course_name", "status",
            "motivation", "line_manager_email", "department", "employee_id",
            "hexco_level", "selected_department", "certification_type", "student_category",
            "preferred_centre", "is_resident", "hostel_name", "room_number",
            "guardian_name", "guardian_contact", "guardian_email", "responsible_party",
            "national_id_doc", "academic_certs_doc", "student_photo",
            "assigned_centre", "assigned_centre_name",
            "reviewer", "reviewer_name", "reviewer_notes",
            "rejection_reason", "more_info_request",
            "code_of_conduct_signed", "code_of_conduct_signed_at",
            "lecturer_signed_off", "lecturer_signed_off_at",
            "lecturer_signed_off_by_name", "lecturer_signoff_notes",
            "escalated", "escalated_at",
            "submitted_at", "reviewed_at", "approved_at", "enrolled_at",
            "created_at", "updated_at",
            "documents", "recent_history",
            "academic_sittings", "qualification_assessment", "qualification_overrides",
            "payment", "enrollment", "certificate",
        )
        read_only_fields = (
            "id", "applicant", "status", "reviewer",
            "created_at", "updated_at",
        )

    def get_applicant_name(self, obj):
        return obj.applicant.full_name

    def get_reviewer_name(self, obj):
        return obj.reviewer.full_name if obj.reviewer else None

    def get_lecturer_signed_off_by_name(self, obj):
        return obj.lecturer_signed_off_by.full_name if obj.lecturer_signed_off_by else None

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
                "reference": p.reference,
                "confirmed_at": p.confirmed_at,
                "confirmed_by_name": p.confirmed_by.full_name if p.confirmed_by else None,
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
                "error_message": e.error_message,
            }
        except Exception:
            return None

    def get_certificate(self, obj):
        try:
            cert = obj.enrollment.certificate
        except Exception:
            return None
        request = self.context.get("request")
        pdf_url = None
        if cert.pdf_file:
            pdf_url = request.build_absolute_uri(cert.pdf_file.url) if request else cert.pdf_file.url
        elif cert.pdf_url:
            pdf_url = cert.pdf_url
        return {
            "id": str(cert.id),
            "certificate_number": cert.certificate_number,
            "issued_at": cert.issued_at,
            "is_revoked": cert.is_revoked,
            "status": cert.status_display,
            "pdf_url": pdf_url,
            "verification_url": cert.verification_url,
        }


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
