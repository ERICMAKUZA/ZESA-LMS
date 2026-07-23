from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        "certificate_number", "user", "course", "issued_at",
        "issued_by", "is_revoked",
    )
    list_filter = ("is_revoked", "issued_at", "course")
    search_fields = ("certificate_number", "user__email", "course__fullname")
    ordering = ("-issued_at",)
    readonly_fields = (
        "certificate_number", "issued_at", "pdf_generated_at", "verification_url",
    )
