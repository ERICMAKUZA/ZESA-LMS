import logging

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_certificate_pdf(self, certificate_id: str):
    """
    Async task: generate PDF for certificate, save to storage,
    then email the student a download link.
    """
    from .models import Certificate
    from .pdf_generator import generate_certificate_pdf as make_pdf

    try:
        cert = Certificate.objects.select_related(
            "user", "course", "enrollment__application__assigned_centre",
        ).get(id=certificate_id)
    except Certificate.DoesNotExist:
        logger.error("generate_certificate_pdf: certificate %s not found", certificate_id)
        return

    try:
        pdf_bytes = make_pdf(cert)

        filename = f"{cert.certificate_number}.pdf"
        cert.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
        cert.pdf_generated_at = timezone.now()
        cert.save(update_fields=["pdf_file", "pdf_generated_at"])

        logger.info("generate_certificate_pdf: PDF generated for %s", cert.certificate_number)

        _send_certificate_email(cert)

    except Exception as exc:
        logger.exception("generate_certificate_pdf: failed for %s: %s", certificate_id, exc)
        raise self.retry(exc=exc)


def _send_certificate_email(cert):
    from django.conf import settings
    from apps.workflows.services import queue_notification

    portal_url = getattr(settings, "PORTAL_BASE_URL", "http://localhost:3000")
    verify_url = cert.verification_url

    queue_notification(
        recipient=cert.user,
        subject=f"Your ZNTC Certificate — {cert.course.fullname}",
        message=(
            f"Dear {cert.user.full_name},\n\n"
            f"Congratulations on successfully completing your programme!\n\n"
            f"Your certificate details:\n"
            f"  Course:        {cert.course.fullname}\n"
            f"  Level:         {cert.get_programme_level_display()}\n"
            f"  Issue Date:    {cert.issue_date.strftime('%d %B %Y')}\n"
            f"  Serial Number: {cert.certificate_number}\n\n"
            f"You can download your certificate and verify it online at:\n"
            f"  {portal_url}/certificates\n\n"
            f"Employers and institutions can verify your certificate at:\n"
            f"  {verify_url}\n\n"
            f"Congratulations once again from the ZNTC team.\n\n"
            f"Regards,\n"
            f"ZESA National Training Centre\n"
            f"Ganges Road, Workington, Harare"
        ),
        application=cert.enrollment.application,
        action_url="/certificates",
    )
