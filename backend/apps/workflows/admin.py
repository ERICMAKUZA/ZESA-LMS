from django.contrib import admin

from .models import ApprovalStep, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("subject", "recipient", "channel", "is_read", "is_sent", "sent_at", "created_at")
    list_filter = ("channel", "is_read", "is_sent")
    search_fields = ("recipient__email", "subject")
    readonly_fields = ("sent_at", "read_at", "created_at")
    ordering = ("-created_at",)


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ("application", "reviewer", "action", "step_order", "acted_at")
    list_filter = ("action",)
    search_fields = ("application__applicant__email",)
    ordering = ("-acted_at",)
    readonly_fields = ("acted_at",)
