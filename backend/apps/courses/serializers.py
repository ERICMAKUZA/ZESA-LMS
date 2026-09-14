import datetime
from rest_framework import serializers

from apps.accounts.models import User

from .models import (
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


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ("id", "name", "moodle_id")


class CourseCategoryWithCountSerializer(serializers.ModelSerializer):
    course_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CourseCategory
        fields = ("id", "name", "course_count")


class CourseSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "moodle_course_id", "shortname", "fullname", "thumbnail_url", "price", "is_active")


class CourseScheduleSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.fullname', read_only=True)
    course_shortname = serializers.CharField(source='course.shortname', read_only=True)
    month_display = serializers.CharField(source='get_month_display', read_only=True)
    category = serializers.CharField(source='course.category.name', read_only=True)
    course_price = serializers.DecimalField(
        source='course.price', max_digits=10, decimal_places=2, read_only=True, allow_null=True
    )
    course_duration_days = serializers.IntegerField(
        source='course.duration_days', read_only=True, allow_null=True
    )
    approximate_start_date = serializers.SerializerMethodField()
    approximate_end_date = serializers.SerializerMethodField()
    places_remaining = serializers.IntegerField(read_only=True)
    lecturer_name = serializers.SerializerMethodField()

    def get_lecturer_name(self, obj):
        return obj.lecturer.full_name if obj.lecturer else None

    def get_approximate_start_date(self, obj):
        return obj.get_approximate_start_date().isoformat()

    def get_approximate_end_date(self, obj):
        return obj.get_approximate_end_date().isoformat()

    class Meta:
        model = CourseSchedule
        fields = [
            'id', 'course', 'course_name', 'course_shortname', 'category',
            'course_price', 'course_duration_days',
            'year', 'month', 'month_display', 'week_in_month',
            'max_capacity', 'enrolled_count', 'places_remaining',
            'status', 'approximate_start_date', 'approximate_end_date', 'notes',
            'lecturer', 'lecturer_name',
        ]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "code", "name", "description", "is_active")


class CourseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseType
        fields = (
            "id", "code", "name", "description", "is_active",
            "requires_qualification_assessment", "default_qualification_profile",
        )


class CertificationTypeSerializer(serializers.ModelSerializer):
    course_type = serializers.PrimaryKeyRelatedField(
        queryset=CourseType.objects.filter(is_active=True)
    )

    class Meta:
        model = CertificationType
        fields = ("id", "course_type", "code", "name", "description", "is_active")


class GradeBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeBand
        fields = ("id", "code", "label", "rank", "points", "is_active")


class QualificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualificationProfile
        fields = (
            "id", "code", "name", "course_type", "max_o_level_sittings",
            "minimum_total_points", "prefer_a_level_sciences", "is_active",
        )

    def validate_course_type(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError("Select an active course type.")
        return value


class QualificationRequirementSerializer(serializers.ModelSerializer):
    minimum_grade_band = serializers.PrimaryKeyRelatedField(
        queryset=GradeBand.objects.filter(is_active=True)
    )

    class Meta:
        model = QualificationRequirement
        fields = (
            "id", "profile", "education_level", "subject_group",
            "minimum_grade_band", "is_required",
        )

    def validate_profile(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Select an active qualification profile.")
        return value


class InitialScheduleSerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2020, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)
    week_in_month = serializers.IntegerField(min_value=1, max_value=4)
    max_capacity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CourseSerializer(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseCategory.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    is_full = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    next_schedule = serializers.SerializerMethodField()
    upcoming_schedules = serializers.SerializerMethodField()
    lecturers = serializers.SerializerMethodField()
    lecturer_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.LECTURER, is_active=True),
        source="lecturers",
        write_only=True,
        many=True,
        required=False,
    )
    course_type = CourseTypeSerializer(read_only=True)
    course_type_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseType.objects.all(),
        source="course_type",
        write_only=True,
        required=False,
        allow_null=True,
    )
    departments = DepartmentSerializer(many=True, read_only=True)
    department_ids = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source="departments",
        write_only=True,
        many=True,
        required=False,
    )
    certification_type_ids = serializers.PrimaryKeyRelatedField(
        queryset=CertificationType.objects.all(),
        source="certification_types",
        write_only=True,
        many=True,
        required=False,
    )
    certification_types = CertificationTypeSerializer(many=True, read_only=True)
    minimum_points_required = serializers.IntegerField(required=False, allow_null=True)
    required_subjects = serializers.ListField(child=serializers.CharField(), required=False)
    qualification_profile = QualificationProfileSerializer(read_only=True)
    qualification_profile_id = serializers.PrimaryKeyRelatedField(
        queryset=QualificationProfile.objects.all(),
        source="qualification_profile",
        write_only=True,
        required=False,
        allow_null=True,
    )
    initial_schedule = InitialScheduleSerializer(write_only=True, required=False)

    def get_lecturers(self, obj):
        request = self.context.get("request")
        if (
            not request
            or not request.user.is_authenticated
            or request.user.role not in (
                User.Role.ADMIN,
                User.Role.SUPERADMIN,
                User.Role.TRAINER,
            )
        ):
            return []
        return [
            {"id": lecturer.id, "full_name": lecturer.full_name, "email": lecturer.email}
            for lecturer in obj.lecturers.all()
        ]

    def validate(self, attrs):
        # If certification types are provided, validate they all belong to the
        # selected course type (when already set or supplied in this payload).
        course_type_supplied = "course_type" in attrs
        course_type = attrs.get("course_type") if course_type_supplied else getattr(
            self.instance, "course_type", None
        )
        if not course_type and (self.instance is None or course_type_supplied):
            raise serializers.ValidationError(
                {"course_type_id": "Select a course type before creating a course."}
            )

        existing_course_type_id = getattr(self.instance, "course_type_id", None)
        if course_type and not course_type.is_active and course_type.id != existing_course_type_id:
            raise serializers.ValidationError(
                {"course_type_id": "Select an active course type."}
            )

        if "departments" in attrs:
            existing_department_ids = set()
            if self.instance is not None:
                existing_department_ids = set(
                    self.instance.departments.values_list("id", flat=True)
                )
            inactive_departments = [
                item.id
                for item in attrs["departments"]
                if not item.is_active and item.id not in existing_department_ids
            ]
            if inactive_departments:
                raise serializers.ValidationError(
                    {"department_ids": "Select active departments only."}
                )

        cert_types = attrs.get("certification_types")
        if cert_types is not None:
            existing_certification_ids = set()
            if self.instance is not None:
                existing_certification_ids = set(
                    self.instance.certification_types.values_list("id", flat=True)
                )
            inactive_certifications = [
                item.id
                for item in cert_types
                if not item.is_active and item.id not in existing_certification_ids
            ]
            if inactive_certifications:
                raise serializers.ValidationError(
                    {"certification_type_ids": "Select active certification options only."}
                )
        if cert_types is None and self.instance is not None:
            cert_types = self.instance.certification_types.all()
        if cert_types:
            if not course_type:
                raise serializers.ValidationError(
                    {"course_type_id": "Select a course type before selecting certification options."}
                )
            invalid = [item.id for item in cert_types if item.course_type_id != course_type.id]
            if invalid:
                raise serializers.ValidationError(
                    {"certification_type_ids": "All certificate options must belong to the selected course type."}
                )

        profile_supplied = "qualification_profile" in attrs
        qualification_profile = attrs.get("qualification_profile") if profile_supplied else getattr(
            self.instance, "qualification_profile", None
        )
        existing_profile_id = getattr(self.instance, "qualification_profile_id", None)
        if (
            qualification_profile
            and not qualification_profile.is_active
            and qualification_profile.id != existing_profile_id
        ):
            raise serializers.ValidationError(
                {"qualification_profile_id": "Select an active qualification profile."}
            )
        if (
            qualification_profile
            and qualification_profile.course_type_id
            and qualification_profile.course_type_id != getattr(course_type, "id", None)
        ):
            raise serializers.ValidationError(
                {"qualification_profile_id": "The qualification profile must match the selected course type."}
            )
        if course_type and course_type.requires_qualification_assessment and not qualification_profile:
            raise serializers.ValidationError(
                {"qualification_profile_id": "Select a qualification profile for this course type."}
            )

        if self.instance is None:
            if not attrs.get("lecturers"):
                raise serializers.ValidationError(
                    {"lecturer_ids": "Assign at least one lecturer to a new course."}
                )
            if not attrs.get("category"):
                raise serializers.ValidationError(
                    {"category_id": "Select a category for the new course."}
                )
            if not attrs.get("initial_schedule"):
                raise serializers.ValidationError(
                    {"initial_schedule": "Add the first course intake before publishing."}
                )
            if not attrs.get("duration_days"):
                raise serializers.ValidationError(
                    {"duration_days": "Set the course duration before adding an intake."}
                )
        elif "lecturers" in attrs and not attrs["lecturers"]:
            raise serializers.ValidationError(
                {"lecturer_ids": "A course must have at least one assigned lecturer."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("initial_schedule", None)
        return super().create(validated_data)

    def get_next_schedule(self, obj):
        today = datetime.date.today()
        qs = obj.schedules.filter(
            status='OPEN',
            year__gte=today.year,
        ).order_by('year', 'month', 'week_in_month')
        for s in qs:
            if s.year > today.year or s.month >= today.month:
                return CourseScheduleSerializer(s).data
        return None

    def get_upcoming_schedules(self, obj):
        today = datetime.date.today()
        qs = obj.schedules.filter(
            year__gte=today.year, status__in=['OPEN', 'FULL']
        ).order_by('year', 'month', 'week_in_month')[:6]
        return CourseScheduleSerializer(qs, many=True).data

    class Meta:
        model = Course
        fields = (
            "id", "moodle_course_id", "shortname", "fullname", "summary",
            "category", "category_id", "category_name",
            "course_type", "course_type_id", "departments", "department_ids",
            "certification_types", "certification_type_ids",
            "minimum_points_required", "required_subjects",
            "qualification_profile", "qualification_profile_id",
            "enrolled_count", "max_capacity",
            "is_active", "requires_approval", "price", "thumbnail_url",
            "duration_days", "level",
            "is_full", "created_at", "updated_at",
            "lecturers", "lecturer_ids", "initial_schedule",
            "next_schedule", "upcoming_schedules",
        )
        read_only_fields = (
            "id", "moodle_course_id", "enrolled_count", "created_at", "updated_at"
        )
