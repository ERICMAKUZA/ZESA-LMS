"""
ZNTC Certificate PDF Generator
Produces an A4 landscape PDF certificate with QR verification code.
"""
import io
import qrcode
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# Brand colours
ZNTC_GREEN       = HexColor('#1a6b3c')   # Dark green
ZNTC_GREEN_LIGHT = HexColor('#e8f5ee')   # Light green background
ZNTC_GOLD        = HexColor('#c8a84b')   # Gold accent
ZNTC_GREY        = HexColor('#4a5568')   # Body text


def _make_qr_image(data: str) -> ImageReader:
    """Generate a QR code and return as a ReportLab ImageReader."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return ImageReader(buf)


def generate_certificate_pdf(certificate, is_duplicate: bool = False) -> bytes:
    """
    Generate a PDF certificate for the given Certificate instance.
    Returns raw PDF bytes.
    """
    page_width, page_height = landscape(A4)   # 297mm x 210mm
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    W, H = page_width, page_height

    # ── Background ──────────────────────────────────────────────────────
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Outer border (double line effect)
    c.setStrokeColor(ZNTC_GREEN)
    c.setLineWidth(4)
    c.rect(10*mm, 8*mm, W - 20*mm, H - 16*mm, fill=0, stroke=1)
    c.setStrokeColor(ZNTC_GOLD)
    c.setLineWidth(1.5)
    c.rect(13*mm, 11*mm, W - 26*mm, H - 22*mm, fill=0, stroke=1)

    # ── DUPLICATE watermark ─────────────────────────────────────────────
    # Large diagonal watermark drawn now (semi-transparent, so it reads
    # fine even where later opaque elements like the header/footer bands
    # sit on top of it). The small footer stamp is deferred until after
    # the footer band is painted below, otherwise that band's opaque fill
    # would hide it.
    if is_duplicate:
        c.saveState()
        c.setFillColor(HexColor('#FF0000'))
        c.setFillAlpha(0.15)
        c.setFont('Helvetica-Bold', 80)
        c.translate(W / 2, H / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, 'DUPLICATE')
        c.restoreState()

    # Green header band
    c.setFillColor(ZNTC_GREEN)
    c.rect(10*mm, H - 44*mm, W - 20*mm, 34*mm, fill=1, stroke=0)

    # ── Header text ─────────────────────────────────────────────────────
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(W / 2, H - 24*mm, 'ZESA NATIONAL TRAINING CENTRE')

    c.setFont('Helvetica', 11)
    c.drawCentredString(W / 2, H - 32*mm, 'Ganges Road, Workington, Harare  |  training@zntc.ac.zw')

    c.setFont('Helvetica', 10)
    c.drawCentredString(W / 2, H - 38*mm, 'ZH/RFP/06/2025 — Accredited Training Provider')

    # ── Gold divider ────────────────────────────────────────────────────
    c.setStrokeColor(ZNTC_GOLD)
    c.setLineWidth(2)
    c.line(25*mm, H - 50*mm, W - 25*mm, H - 50*mm)

    # ── Certificate title ───────────────────────────────────────────────
    c.setFillColor(ZNTC_GREEN)
    c.setFont('Helvetica-Bold', 18)

    level_display = {
        'NC': 'NATIONAL CERTIFICATE',
        'ND': 'NATIONAL DIPLOMA',
        '':   'CERTIFICATE OF COMPLETION',
    }.get(certificate.programme_level, 'CERTIFICATE OF COMPLETION')

    c.drawCentredString(W / 2, H - 62*mm, 'CERTIFICATE OF ACHIEVEMENT')
    c.setFont('Helvetica', 11)
    c.setFillColor(ZNTC_GREY)
    c.drawCentredString(W / 2, H - 70*mm, f'({level_display})')

    # ── Body text ───────────────────────────────────────────────────────
    c.setFont('Helvetica', 12)
    c.setFillColor(ZNTC_GREY)
    c.drawCentredString(W / 2, H - 82*mm, 'This is to certify that')

    # Student name — large
    student_name = certificate.user.full_name
    c.setFont('Helvetica-Bold', 28)
    c.setFillColor(ZNTC_GREEN)
    c.drawCentredString(W / 2, H - 98*mm, student_name)

    # Underline below name
    name_width = c.stringWidth(student_name, 'Helvetica-Bold', 28)
    c.setStrokeColor(ZNTC_GOLD)
    c.setLineWidth(1)
    underline_x = (W - name_width) / 2
    c.line(underline_x, H - 100*mm, underline_x + name_width, H - 100*mm)

    c.setFont('Helvetica', 12)
    c.setFillColor(ZNTC_GREY)
    c.drawCentredString(W / 2, H - 109*mm, 'has successfully completed the programme')

    # Course name
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(ZNTC_GREEN)
    c.drawCentredString(W / 2, H - 120*mm, certificate.course.fullname)

    c.setFont('Helvetica', 11)
    c.setFillColor(ZNTC_GREY)
    centre_name = certificate.centre.name if certificate.centre else 'ZNTC Harare'
    c.drawCentredString(
        W / 2, H - 128*mm,
        f'at {centre_name}  |  {certificate.issue_date.strftime("%d %B %Y")}'
    )

    # ── Student ID ──────────────────────────────────────────────────────
    if certificate.student_id_snapshot:
        c.setFont('Helvetica', 9)
        c.setFillColor(ZNTC_GREY)
        c.drawCentredString(
            W / 2, H - 135*mm,
            f'Student ID: {certificate.student_id_snapshot}'
        )

    # ── Signature lines ─────────────────────────────────────────────────
    sig_y = H - 155*mm
    # Left signature
    c.setStrokeColor(ZNTC_GREY)
    c.setLineWidth(0.75)
    c.line(25*mm, sig_y, 95*mm, sig_y)
    c.setFont('Helvetica', 9)
    c.setFillColor(ZNTC_GREY)
    c.drawCentredString(60*mm, sig_y - 5*mm, 'Principal / Director of Training')
    c.drawCentredString(60*mm, sig_y - 10*mm, 'ZESA National Training Centre')

    # Right signature
    c.line(W - 95*mm, sig_y, W - 25*mm, sig_y)
    c.drawCentredString(W - 60*mm, sig_y - 5*mm, 'HEXCO Examinations Officer')
    c.drawCentredString(W - 60*mm, sig_y - 10*mm, 'Ministry of Higher & Tertiary Education')

    # ── Serial number footer ─────────────────────────────────────────────
    c.setFillColor(ZNTC_GREEN_LIGHT)
    c.rect(10*mm, 8*mm, W - 20*mm, 14*mm, fill=1, stroke=0)

    c.setFont('Helvetica', 8)
    c.setFillColor(ZNTC_GREY)
    c.drawString(
        16*mm, 14*mm,
        f'Serial No: {certificate.certificate_number}   |   '
        f'Issued: {certificate.issue_date.strftime("%d %B %Y")}   |   '
        f'Verify at: {certificate.verification_url}'
    )

    if is_duplicate:
        c.setFillColor(HexColor('#FF0000'))
        c.setFont('Helvetica-Bold', 9)
        c.drawString(16*mm, 19*mm, 'DUPLICATE COPY')

    # ── QR Code ─────────────────────────────────────────────────────────
    qr_img = _make_qr_image(certificate.verification_url)
    qr_size = 28*mm
    c.drawImage(qr_img, W - 44*mm, 10*mm, width=qr_size, height=qr_size)
    c.setFont('Helvetica', 6)
    c.setFillColor(ZNTC_GREY)
    c.drawCentredString(W - 30*mm, 9*mm, 'Scan to verify')

    c.save()
    buf.seek(0)
    return buf.read()
