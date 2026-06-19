import uuid

from django.conf import settings
from django.db import models


class Certificate(models.Model):
    enrollment = models.OneToOneField(
        "enrollments.Enrollment",
        on_delete=models.CASCADE,
        related_name="certificate",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    certificate_number = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    pdf_url = models.URLField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Certificate {self.certificate_number} – {self.user} – {self.course.shortname}"
