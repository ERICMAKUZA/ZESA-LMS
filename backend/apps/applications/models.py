import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


def application_upload_path(instance, filename):
    import datetime, os
    today = datetime.date.today()
    ext = os.path.splitext(filename)[1].lower()
    return f"application_docs/{today.year}/{today.month:02d}/{instance.ref or 'draft'}{ext}"


class ApplicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    MORE_INFO_REQUESTED = "MORE_INFO_REQUESTED", "More Info Requested"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    PAYMENT_PENDING = "PAYMENT_PENDING", "Payment Pending"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Payment Confirmed"
    ENROLLED = "ENROLLED", "Enrolled"
    DE_ENROLLED = "DE_ENROLLED", "De-enrolled"
    CERTIFIED = "CERTIFIED", "Certified"


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    status = models.CharField(
        max_length=25,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
    )
    motivation = models.TextField()
    line_manager_email = models.EmailField()
    department = models.CharField(max_length=150)
    employee_id = models.CharField(max_length=50, blank=True)
    preferred_centre = models.ForeignKey(
        'centres.Centre', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='preferred_applications'
    )
    assigned_centre = models.ForeignKey(
        'centres.Centre', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_applications'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_reviews",
    )
    reviewer_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    more_info_request = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    enrolled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    HEXCO_LEVEL_CHOICES = [
        ('NC', 'National Certificate (NC)'),
        ('ND', 'National Diploma (ND)'),
    ]
    DEPARTMENT_CHOICES = [
        ('ELECTRICAL', 'Electrical Engineering'),
        ('TELECOMS', 'Telecommunications'),
        ('MECHANICAL', 'Mechanical Engineering'),
    ]

    hexco_level = models.CharField(
        max_length=2, choices=HEXCO_LEVEL_CHOICES, blank=True, default=''
    )

    STUDENT_CATEGORY_CHOICES = [
        ('DIRECT', 'Direct Applicant'),
        ('APPRENTICE', 'Apprentice (Company-Sponsored)'),
        ('INTERNAL', 'Internal ZESA Staff'),
    ]

    student_category = models.CharField(
        max_length=12, choices=STUDENT_CATEGORY_CHOICES, blank=True, default=''
    )
    is_resident = models.BooleanField(
        default=False,
        help_text="True if student will stay in ZNTC hostel"
    )
    hostel_name = models.CharField(max_length=100, blank=True, default='')
    room_number = models.CharField(max_length=20, blank=True, default='')

    # Guardian / next of kin
    guardian_name = models.CharField(max_length=200, blank=True, default='')
    guardian_contact = models.CharField(max_length=20, blank=True, default='')
    guardian_email = models.EmailField(blank=True, default='')

    # Financial responsible party (person or company name)
    responsible_party = models.CharField(max_length=200, blank=True, default='')

    ref = models.CharField(max_length=20, unique=True, blank=True, db_index=True)

    SOURCE_CHOICES = [
        ('ONLINE', 'Online (Student Self-Service)'),
        ('WALK_IN', 'Walk-in (Staff Captured)'),
    ]

    source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default='ONLINE'
    )
    staff_captured_by = models.ForeignKey(
        'accounts.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='captured_applications',
        help_text="Set when source=WALK_IN; the staff member who entered this application"
    )

    national_id_doc = models.FileField(
        upload_to=application_upload_path, null=True, blank=True,
        help_text="National ID card or passport scan (PDF, JPG, PNG)"
    )
    academic_certs_doc = models.FileField(
        upload_to=application_upload_path, null=True, blank=True,
        help_text="Academic certificates (PDF)"
    )
    student_photo = models.ImageField(
        upload_to=application_upload_path, null=True, blank=True,
        help_text="Passport-size photo (JPG, PNG)"
    )

    escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)

    code_of_conduct_signed = models.BooleanField(default=False)
    code_of_conduct_signed_at = models.DateTimeField(null=True, blank=True)

    lecturer_signed_off = models.BooleanField(default=False)
    lecturer_signed_off_at = models.DateTimeField(null=True, blank=True)
    lecturer_signed_off_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='lecturer_signoffs',
        limit_choices_to={'role': 'LECTURER'},
    )
    lecturer_signoff_notes = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        ordering = ["-created_at"]
        # DB unique_together is intentionally omitted: one active application per
        # course per user is enforced in clean(), allowing re-application after REJECTED.

    def __str__(self):
        return f"{self.applicant} → {self.course.shortname} [{self.status}]"

    def clean(self):
        if self.status != ApplicationStatus.REJECTED:
            qs = (
                Application.objects.filter(applicant=self.applicant, course=self.course)
                .exclude(pk=self.pk)
                .exclude(status=ApplicationStatus.REJECTED)
            )
            if qs.exists():
                raise ValidationError(
                    "An active application already exists for this course."
                )

    # ── Ref generation ────────────────────────────────────────────────────────

    @classmethod
    def _generate_ref(cls):
        import datetime
        year = datetime.date.today().year
        prefix = f"ZNTC-{year}-"
        last = (
            cls.objects
            .filter(ref__startswith=prefix)
            .order_by('ref')
            .values_list('ref', flat=True)
            .last()
        )
        if last:
            last_seq = int(last.split('-')[-1])
        else:
            last_seq = 0
        return f"{prefix}{str(last_seq + 1).zfill(4)}"

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = self.__class__._generate_ref()
        super().save(*args, **kwargs)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _record_transition(self, to_status, changed_by=None, notes=""):
        ApplicationStatusHistory.objects.create(
            application=self,
            from_status=self.status,
            to_status=to_status,
            changed_by=changed_by,
            changed_by_ec_number=getattr(changed_by, 'ec_number', '') or '',
            changed_by_name_snapshot=changed_by.full_name if changed_by else 'System',
            notes=notes,
        )

    # ── State machine ─────────────────────────────────────────────────────────

    def submit(self):
        allowed = (ApplicationStatus.DRAFT, ApplicationStatus.MORE_INFO_REQUESTED)
        if self.status not in allowed:
            raise ValueError(f"Cannot submit from status '{self.status}'.")
        self._record_transition(ApplicationStatus.SUBMITTED)
        self.status = ApplicationStatus.SUBMITTED
        self.submitted_at = timezone.now()
        self.save(update_fields=["status", "submitted_at", "updated_at"])

    def start_review(self, reviewer):
        if self.status != ApplicationStatus.SUBMITTED:
            raise ValueError(f"Cannot start review from status '{self.status}'.")
        self._record_transition(ApplicationStatus.UNDER_REVIEW, changed_by=reviewer)
        self.status = ApplicationStatus.UNDER_REVIEW
        self.reviewer = reviewer
        self.save(update_fields=["status", "reviewer", "updated_at"])

    def request_more_info(self, notes):
        if self.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError(f"Cannot request more info from status '{self.status}'.")
        self._record_transition(
            ApplicationStatus.MORE_INFO_REQUESTED, changed_by=self.reviewer, notes=notes
        )
        self.status = ApplicationStatus.MORE_INFO_REQUESTED
        self.more_info_request = notes
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "more_info_request", "reviewed_at", "updated_at"])

    def approve(self, notes=""):
        if self.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError(f"Cannot approve from status '{self.status}'.")
        self._record_transition(
            ApplicationStatus.APPROVED, changed_by=self.reviewer, notes=notes
        )
        self.status = ApplicationStatus.APPROVED
        self.reviewer_notes = notes
        self.approved_at = timezone.now()
        self.reviewed_at = timezone.now()
        self.save(
            update_fields=["status", "reviewer_notes", "approved_at", "reviewed_at", "updated_at"]
        )

    def reject(self, reason):
        if self.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError(f"Cannot reject from status '{self.status}'.")
        self._record_transition(
            ApplicationStatus.REJECTED, changed_by=self.reviewer, notes=reason
        )
        self.status = ApplicationStatus.REJECTED
        self.rejection_reason = reason
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "rejection_reason", "reviewed_at", "updated_at"])

    def mark_payment_pending(self):
        if self.status != ApplicationStatus.APPROVED:
            raise ValueError(f"Cannot mark payment pending from status '{self.status}'.")
        self._record_transition(ApplicationStatus.PAYMENT_PENDING)
        self.status = ApplicationStatus.PAYMENT_PENDING
        self.save(update_fields=["status", "updated_at"])

    def confirm_payment(self):
        if self.status != ApplicationStatus.PAYMENT_PENDING:
            raise ValueError(f"Cannot confirm payment from status '{self.status}'.")
        self._record_transition(ApplicationStatus.PAYMENT_CONFIRMED)
        self.status = ApplicationStatus.PAYMENT_CONFIRMED
        self.save(update_fields=["status", "updated_at"])

    def enroll(self):
        if not self.code_of_conduct_signed:
            raise ValueError("Student must sign the code of conduct before enrolment.")
        if self.status != ApplicationStatus.PAYMENT_CONFIRMED:
            raise ValueError(f"Cannot enroll from status '{self.status}'.")
        self._record_transition(ApplicationStatus.ENROLLED)
        self.status = ApplicationStatus.ENROLLED
        self.enrolled_at = timezone.now()
        self.save(update_fields=["status", "enrolled_at", "updated_at"])
        if self.applicant and not self.applicant.student_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            with transaction.atomic():
                self.applicant.student_id = User.generate_student_id(
                    department=self.department or ''
                )
                self.applicant.save(update_fields=['student_id'])
        from apps.enrollments.models import Enrollment
        from apps.enrollments.tasks import sync_to_moodle
        enrollment, _ = Enrollment.objects.get_or_create(
            application=self,
            defaults={'moodle_course_id': self.course.moodle_course_id or 0},
        )
        sync_to_moodle.delay(str(enrollment.pk))

    def certify(self):
        if self.status != ApplicationStatus.ENROLLED:
            raise ValueError(f"Cannot certify from status '{self.status}'.")
        self._record_transition(ApplicationStatus.CERTIFIED)
        self.status = ApplicationStatus.CERTIFIED
        self.save(update_fields=["status", "updated_at"])

    def lecturer_sign_off(self, lecturer, notes=""):
        """
        Lecturer marks a student as having completed the course (FRS §3.3).
        Certificate issuance is triggered separately by the caller via
        Certificate.issue_from_enrollment(), which also calls certify().
        """
        if self.status != ApplicationStatus.ENROLLED:
            raise ValueError(
                f"Cannot sign off: application {self.ref} "
                f"is {self.status}, expected ENROLLED."
            )
        if self.lecturer_signed_off:
            raise ValueError("Student has already been signed off.")
        self._record_transition(
            self.status, changed_by=lecturer,
            notes=f"Lecturer sign-off by {lecturer.full_name}. Notes: {notes or 'None'}.",
        )
        self.lecturer_signed_off = True
        self.lecturer_signed_off_at = timezone.now()
        self.lecturer_signed_off_by = lecturer
        self.lecturer_signoff_notes = notes
        self.save(update_fields=[
            "lecturer_signed_off", "lecturer_signed_off_at",
            "lecturer_signed_off_by", "lecturer_signoff_notes",
        ])


class ApplicationDocument(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to="application_docs/%Y/%m/")
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Application Document"
        verbose_name_plural = "Application Documents"
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.filename} (application {self.application_id})"


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="history",
    )
    from_status = models.CharField(max_length=25)
    to_status = models.CharField(max_length=25)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="status_changes",
    )
    # Snapshots of changed_by's identity at the time of the event, so the
    # audit trail (FRS: "name and EC number of ZNTC staff member who
    # actioned") survives the actor's account being edited or deactivated.
    changed_by_ec_number = models.CharField(max_length=20, blank=True, default='')
    changed_by_name_snapshot = models.CharField(max_length=200, blank=True, default='')
    notes = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Application Status History"
        verbose_name_plural = "Application Status Histories"
        ordering = ["changed_at"]

    def __str__(self):
        return (
            f"Application {self.application_id}: "
            f"{self.from_status} → {self.to_status} "
            f"at {self.changed_at:%Y-%m-%d %H:%M}"
        )
