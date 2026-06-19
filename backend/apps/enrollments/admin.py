from django.contrib import admin
from django.utils.html import format_html

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "application_link", "status", "moodle_user_id",
        "enrolled_at", "last_access",
    )
    list_filter = ("status",)
    search_fields = ("application__applicant__email", "application__course__shortname")
    readonly_fields = (
        "id", "created_at", "enrolled_at", "unenrolled_at",
        "moodle_user_id", "completion_status", "last_access", "error_message",
    )
    ordering = ("-created_at",)
    fieldsets = (
        ("Enrollment", {
            "fields": ("id", "application", "status", "moodle_user_id", "moodle_course_id"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "enrolled_at", "unenrolled_at", "last_access"),
        }),
        ("Moodle Data", {
            "fields": ("completion_status",),
            "classes": ("collapse",),
        }),
        ("Error", {
            "fields": ("error_message",),
        }),
    )

    @admin.display(description="Application")
    def application_link(self, obj):
        from django.urls import reverse
        url = reverse("admin:applications_application_change", args=[obj.application_id])
        return format_html('<a href="{}">{}</a>', url, str(obj.application))
