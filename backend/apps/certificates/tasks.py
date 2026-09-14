import logging

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_certificate_pdf(self, certificate_id: str):
    """
    Async task: generate PDF for certificate, save to storage,
    then store it for the student to download.
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

    except Exception as exc:
        logger.exception("generate_certificate_pdf: failed for %s: %s", certificate_id, exc)
        raise self.retry(exc=exc)
