from django.contrib import admin

from .models import Course, CourseCategory, CourseSchedule, Enquiry


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


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'course', 'year', 'month', 'week_in_month',
        'status', 'enrolled_count', 'max_capacity', 'places_remaining',
    ]
    list_filter = ['year', 'month', 'status', 'course__category']
    list_editable = ['status', 'max_capacity']
    ordering = ['year', 'month', 'week_in_month']
    search_fields = ['course__fullname', 'course__shortname']


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email', 'phone', 'enquiry_type',
        'course', 'status', 'submitted_at',
    ]
    list_filter = ['enquiry_type', 'status', 'submitted_at']
    list_editable = ['status']
    search_fields = ['full_name', 'email', 'message']
    readonly_fields = [
        'submitted_at', 'full_name', 'email', 'phone',
        'message', 'enquiry_type', 'course', 'organisation',
    ]
    fieldsets = [
        ('Enquiry Details', {
            'fields': [
                'full_name', 'email', 'phone', 'organisation',
                'enquiry_type', 'course', 'message', 'submitted_at',
            ],
        }),
        ('Admin', {
            'fields': ['status', 'admin_notes', 'resolved_at'],
        }),
    ]
