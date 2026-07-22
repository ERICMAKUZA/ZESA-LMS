from django.contrib import admin

from .models import Payment, SAPSyncLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "amount", "currency", "method", "status", "reference", "initiated_at", "confirmed_at")
    list_filter = ("status", "method", "currency")
    search_fields = ("application__applicant__email", "paynow_reference", "sap_document_number", "reference")
    readonly_fields = ("id", "initiated_at", "confirmed_at", "confirmed_by", "raw_webhook_payload")
    ordering = ("-initiated_at",)
    fieldsets = (
        ("Payment", {
            "fields": ("id", "application", "amount", "currency", "method", "status"),
        }),
        ("Manual / Reference", {
            "fields": ("reference", "confirmed_by"),
        }),
        ("Paynow", {
            "fields": ("paynow_reference", "paynow_poll_url", "paynow_redirect_url", "raw_webhook_payload"),
            "classes": ("collapse",),
        }),
        ("SAP", {
            "fields": ("sap_document_number", "sap_cost_center"),
            "classes": ("collapse",),
        }),
        ("Outcome", {
            "fields": ("initiated_at", "confirmed_at", "failed_reason"),
        }),
    )


@admin.register(SAPSyncLog)
class SAPSyncLogAdmin(admin.ModelAdmin):
    list_display = ("synced_at", "records_processed", "records_matched", "success")
    list_filter = ("success",)
    readonly_fields = ("synced_at", "records_processed", "records_matched", "errors", "success")
    ordering = ("-synced_at",)
