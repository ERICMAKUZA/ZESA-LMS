from django.contrib import admin

from .models import Application, ApplicationDocument, ApplicationStatusHistory


class ApplicationStatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "notes", "changed_at")
    ordering = ("-changed_at",)
    can_delete = False


class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0
    readonly_fields = ("filename", "file", "uploaded_at")
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("ref", "applicant", "course", "status", "reviewer", "submitted_at")
    list_filter = ("status", "course")
    search_fields = ("ref", "applicant__email", "applicant__first_name", "applicant__last_name")
    readonly_fields = (
        "id", "created_at", "updated_at",
        "submitted_at", "reviewed_at", "approved_at", "enrolled_at",
    )
    ordering = ("-created_at",)
    inlines = [ApplicationStatusHistoryInline, ApplicationDocumentInline]
    fieldsets = (
        ("Application", {
            "fields": ("id", "applicant", "course", "status"),
        }),
        ("Applicant Details", {
            "fields": ("motivation", "line_manager_email", "department", "employee_id"),
        }),
        ("Review", {
            "fields": ("reviewer", "reviewer_notes", "rejection_reason", "more_info_request"),
        }),
        ("Timestamps", {
            "fields": ("submitted_at", "reviewed_at", "approved_at", "enrolled_at", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("application", "from_status", "to_status", "changed_by", "changed_at")
    list_filter = ("to_status",)
    search_fields = ("application__applicant__email",)
    readonly_fields = ("application", "from_status", "to_status", "changed_by", "notes", "changed_at")
    ordering = ("-changed_at",)
