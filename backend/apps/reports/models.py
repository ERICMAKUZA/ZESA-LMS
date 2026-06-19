from django.conf import settings
from django.db import models


class Report(models.Model):
    class ReportType(models.TextChoices):
        ENROLLMENT_SUMMARY = "ENROLLMENT_SUMMARY", "Enrollment Summary"
        PAYMENT_SUMMARY = "PAYMENT_SUMMARY", "Payment Summary"
        COMPLETION_RATES = "COMPLETION_RATES", "Completion Rates"
        DEPARTMENT_USAGE = "DEPARTMENT_USAGE", "Department Usage"
        CERTIFICATE_ISSUANCE = "CERTIFICATE_ISSUANCE", "Certificate Issuance"

    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=ReportType.choices)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_reports",
    )
    parameters = models.JSONField(default=dict, blank=True)
    file_url = models.URLField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.title} [{self.report_type}] – {self.generated_at:%Y-%m-%d}"
