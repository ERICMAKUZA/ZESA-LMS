import io
import logging

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_certificate_pdf(self, certificate_id: str):
    from .models import Certificate

    try:
        cert = Certificate.objects.select_related("user", "course").get(id=certificate_id)
    except Certificate.DoesNotExist:
        logger.error("generate_certificate_pdf: certificate %s not found", certificate_id)
        return

    try:
        pdf_bytes = _render_pdf(cert)
    except Exception as exc:
        logger.exception("generate_certificate_pdf: failed for %s: %s", certificate_id, exc)
        raise self.retry(exc=exc)

    cert.pdf_file.save(f"{cert.certificate_number}.pdf", ContentFile(pdf_bytes), save=False)
    cert.pdf_generated_at = timezone.now()
    cert.save(update_fields=["pdf_file", "pdf_generated_at"])


def _render_pdf(cert) -> bytes:
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(width, height))

    c.setStrokeColor(HexColor("#1e3a8a"))
    c.setLineWidth(4)
    c.rect(1.2 * cm, 1.2 * cm, width - 2.4 * cm, height - 2.4 * cm)

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(HexColor("#1e3a8a"))
    c.drawCentredString(width / 2, height - 4 * cm, "ZESA National Training Centre")

    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#374151"))
    c.drawCentredString(width / 2, height - 5.2 * cm, "Certificate of Completion")

    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, height - 7.5 * cm, "This is to certify that")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(HexColor("#111827"))
    c.drawCentredString(width / 2, height - 9 * cm, cert.user.full_name)

    c.setFont("Helvetica", 13)
    c.setFillColor(HexColor("#374151"))
    c.drawCentredString(width / 2, height - 10.5 * cm, "has successfully completed")

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(HexColor("#1e3a8a"))
    c.drawCentredString(width / 2, height - 12 * cm, cert.course.fullname)

    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#6b7280"))
    c.drawString(2.5 * cm, 2.2 * cm, f"Certificate No: {cert.certificate_number}")
    c.drawString(2.5 * cm, 1.7 * cm, f"Issued: {cert.issued_at:%d %B %Y}")
    c.drawRightString(width - 2.5 * cm, 1.7 * cm, f"Verify at: {cert.verification_url}")

    c.showPage()
    c.save()
    return buf.getvalue()
