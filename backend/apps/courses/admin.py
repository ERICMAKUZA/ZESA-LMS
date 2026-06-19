from django.contrib import admin

from .models import Course, CourseCategory


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "moodle_id")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("shortname", "fullname", "category", "enrolled_count", "max_capacity", "is_active", "requires_approval", "price")
    list_filter = ("is_active", "requires_approval", "category")
    search_fields = ("shortname", "fullname")
    ordering = ("fullname",)
    readonly_fields = ("created_at", "updated_at")
