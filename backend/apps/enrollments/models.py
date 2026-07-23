import uuid

from django.conf import settings
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

    # FRS §3.2: formal per-student enrolment record — the specific intake,
    # its start/end dates, and an active/suspended status. Kept separate from
    # `status` above, which tracks the Moodle *sync* process (PENDING →
    # ENROLLING → ENROLLED/FAILED) rather than the student's academic
    # standing — a student can be academically suspended while their Moodle
    # account stays synced, or vice versa.
    schedule = models.ForeignKey(
        "courses.CourseSchedule",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="enrollments",
        help_text="The specific intake/schedule the student is enrolled in",
    )
    start_date = models.DateField(
        null=True, blank=True, help_text="Course commencement date for this student"
    )
    end_date = models.DateField(
        null=True, blank=True, help_text="Expected course completion date"
    )
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True, default='')
    suspended_at = models.DateTimeField(null=True, blank=True)
    completion_status = models.JSONField(null=True, blank=True)
    last_access = models.DateTimeField(null=True, blank=True)
    moodle_temp_password = models.CharField(max_length=50, blank=True, default='')
    error_message = models.CharField(max_length=500, blank=True, null=True)
    de_enrolment_reason = models.CharField(max_length=500, blank=True, default='')
    de_enrolment_type = models.CharField(
        max_length=10,
        choices=[('MANDATORY', 'Mandatory'), ('VOLUNTARY', 'Voluntary')],
        blank=True,
        default='',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        ordering = ["-created_at"]

    @property
    def moodle_course_url(self) -> str:
        base = settings.MOODLE_BASE_URL.rstrip("/")
        return f"{base}/course/view.php?id={self.moodle_course_id}"

    def suspend(self, reason: str):
        self.is_suspended = True
        self.suspension_reason = reason
        self.suspended_at = timezone.now()
        self.save(update_fields=["is_suspended", "suspension_reason", "suspended_at"])

    def reinstate(self):
        self.is_suspended = False
        self.suspended_at = None
        self.save(update_fields=["is_suspended", "suspended_at"])

    def __str__(self):
        return (
            f"{self.application.applicant.email} → "
            f"{self.application.course.shortname} ({self.status})"
        )
