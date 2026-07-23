import datetime

from django.db.models import Count, Q
from rest_framework import serializers

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
            "next_schedule", "upcoming_schedules",
        )
        read_only_fields = ("id", "enrolled_count", "created_at", "updated_at")
