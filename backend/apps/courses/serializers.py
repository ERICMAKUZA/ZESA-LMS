from rest_framework import serializers

from .models import Course, CourseCategory


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ("id", "name", "moodle_id")


class CourseSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "moodle_course_id", "shortname", "fullname", "thumbnail_url", "price", "is_active")


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

    class Meta:
        model = Course
        fields = (
            "id", "moodle_course_id", "shortname", "fullname", "summary",
            "category", "category_id", "enrolled_count", "max_capacity",
            "is_active", "requires_approval", "price", "thumbnail_url",
            "is_full", "created_at", "updated_at",
        )
        read_only_fields = ("id", "enrolled_count", "created_at", "updated_at")
