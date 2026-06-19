import uuid

from django.db import models
from django.utils import timezone


class EnrollmentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ENROLLING = "ENROLLING", "Enrolling"
    ENROLLED = "ENROLLED", "Enrolled"
    FAILED = "FAILED", "Failed"
    UNENROLLED = "UNENROLLED", "Unenrolled"


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="enrollment",
    )
    moodle_user_id = models.IntegerField(null=True, blank=True)
    moodle_course_id = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.PENDING,
    )
    enrolled_at = models.DateTimeField(null=True, blank=True)
    unenrolled_at = models.DateTimeField(null=True, blank=True)
    completion_status = models.JSONField(null=True, blank=True)
    last_access = models.DateTimeField(null=True, blank=True)
    error_message = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.application.applicant.email} → "
            f"{self.application.course.shortname} ({self.status})"
        )
