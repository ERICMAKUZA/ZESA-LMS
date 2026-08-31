import datetime

from django.db.models import Count, Q
from rest_framework import serializers

from apps.accounts.models import User

from .models import Course, CourseCategory, CourseSchedule


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
    initial_schedule = InitialScheduleSerializer(write_only=True, required=False)

    def get_lecturers(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or not request.user.is_admin:
            return []
        return [
            {"id": lecturer.id, "full_name": lecturer.full_name, "email": lecturer.email}
            for lecturer in obj.lecturers.all()
        ]

    def validate(self, attrs):
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
