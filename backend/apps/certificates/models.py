import uuid

from django.conf import settings
from django.db import models, transaction


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
    pdf_file = models.FileField(upload_to="certificates/pdf/%Y/", null=True, blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="issued_certificates",
        help_text="Admin who manually issued this certificate, blank if auto-issued from a Moodle completion sync",
    )

    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="revoked_certificates",
    )
    revocation_reason = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Certificate {self.certificate_number} – {self.user} – {self.course.shortname}"

    @property
    def verification_url(self):
        base = getattr(settings, "PORTAL_BASE_URL", "http://localhost:3000")
        return f"{base.rstrip('/')}/verify/{self.certificate_number}"

    @property
    def status_display(self):
        return "REVOKED" if self.is_revoked else "VALID"

    # ── Convenience accessors for PDF rendering ─────────────────────────────
    # The certificate doesn't snapshot these itself (unlike name/course, which
    # live directly on the row); they're read live off the application at
    # render time via the enrollment relation.
    @property
    def centre(self):
        return self.enrollment.application.assigned_centre

    @property
    def issue_date(self):
        return self.issued_at.date()

    @property
    def student_id_snapshot(self):
        return self.user.student_id or ""

    @property
    def programme_level(self):
        return self.enrollment.application.hexco_level

    def get_programme_level_display(self):
        return {
            "NC": "National Certificate (NC)",
            "ND": "National Diploma (ND)",
        }.get(self.programme_level, "Short Course")

    # ── Certificate number generation ───────────────────────────────────────
    # Race-safe: uses a Postgres advisory lock keyed on the prefix, since a
    # plain SELECT ... FOR UPDATE takes no lock when zero rows exist yet for
    # that year, which lets concurrent issuances race on the first serial.
    @classmethod
    def generate_number(cls, year: int = None) -> str:
        import datetime
        from django.db import connection

        if year is None:
            year = datetime.date.today().year
        prefix = f"ZNTC-CERT-{year}-"
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [prefix])
            last = (
                cls.objects
                .select_for_update()
                .filter(certificate_number__startswith=prefix)
                .order_by("certificate_number")
                .values_list("certificate_number", flat=True)
                .last()
            )
            last_seq = int(last.split("-")[-1]) if last else 0
            # 6-digit zero-padded (supports up to 999,999 per year). Existing
            # 4-digit certificate numbers remain valid — the format is
            # self-describing and verification works by exact string match.
            return f"{prefix}{str(last_seq + 1).zfill(6)}"

    # ── Issue certificate from an enrollment ────────────────────────────────
    @classmethod
    def issue_from_enrollment(cls, enrollment, issued_by=None):
        """
        Create and issue a certificate for an ENROLLED application's
        enrollment. Transitions the application ENROLLED -> CERTIFIED via
        the existing Application.certify() state machine method.
        Raises ValueError if the application isn't ENROLLED or a
        certificate already exists for this enrollment.
        """
        from apps.applications.models import ApplicationStatus

        application = enrollment.application
        if application.status != ApplicationStatus.ENROLLED:
            raise ValueError(
                f"Cannot issue certificate: application {application.ref} "
                f"is {application.status}, expected ENROLLED."
            )
        if hasattr(enrollment, "certificate"):
            raise ValueError(
                f"Certificate already exists for {application.ref}: "
                f"{enrollment.certificate.certificate_number}"
            )

        with transaction.atomic():
            cert = cls.objects.create(
                enrollment=enrollment,
                user=application.applicant,
                course=application.course,
                certificate_number=cls.generate_number(),
                issued_by=issued_by,
            )
            application.certify()

        from apps.certificates.tasks import generate_certificate_pdf
        generate_certificate_pdf.delay(str(cert.id))

        return cert

    def revoke(self, revoked_by, reason: str):
        from django.utils import timezone

        if self.is_revoked:
            raise ValueError("Certificate is already revoked.")
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.revocation_reason = reason
        self.save(update_fields=["is_revoked", "revoked_at", "revoked_by", "revocation_reason"])
