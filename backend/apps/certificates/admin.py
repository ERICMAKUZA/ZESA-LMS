from django.contrib import admin
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        "certificate_number", "user", "course", "issued_at",
        "issued_by", "is_revoked", "print_duplicate_link",
    )
    list_filter = ("is_revoked", "issued_at", "course")
    search_fields = ("certificate_number", "user__email", "course__fullname")
    ordering = ("-issued_at",)
    readonly_fields = (
        "certificate_number", "issued_at", "pdf_generated_at", "verification_url",
    )

    # A plain link to the DRF /api/certs/<pk>/download/ endpoint won't work
    # from here — it only accepts JWT bearer auth, not the Django admin
    # session. This is a separate, session-authenticated admin view that
    # reuses the same pdf_generator function directly instead.
    def get_urls(self):
        custom = [
            path(
                "<int:certificate_id>/print-duplicate/",
                self.admin_site.admin_view(self.print_duplicate_view),
                name="certificates_certificate_print_duplicate",
            ),
        ]
        return custom + super().get_urls()

    def print_duplicate_view(self, request, certificate_id):
        from .pdf_generator import generate_certificate_pdf

        cert = self.get_object(request, certificate_id)
        if cert is None:
            return HttpResponseNotFound("Certificate not found.")
        pdf_bytes = generate_certificate_pdf(cert, is_duplicate=True)
        filename = f"{cert.certificate_number}_DUPLICATE.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @admin.display(description="Duplicate")
    def print_duplicate_link(self, obj):
        url = reverse("admin:certificates_certificate_print_duplicate", args=[obj.pk])
        return format_html('<a href="{}">Print Duplicate</a>', url)
