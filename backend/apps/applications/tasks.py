import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def notify_application_submitted(self, application_id):
    from .models import Application

    try:
        app = Application.objects.select_related("applicant", "course").get(id=application_id)
    except Application.DoesNotExist:
        logger.error("notify_application_submitted: application %s not found", application_id)
        return

    User = get_user_model()
    recipients = list(
        User.objects.filter(
            role__in=("REVIEWER", "ADMIN", "SUPERADMIN"),
            is_active=True,
        ).values_list("email", flat=True)
    )
    if not recipients:
        logger.warning("notify_application_submitted: no reviewer/admin users found")
        return

    subject = f"New application: {app.applicant.full_name} for {app.course.fullname}"
    message = (
        f"A new training application has been submitted.\n\n"
        f"Applicant : {app.applicant.full_name} ({app.applicant.email})\n"
        f"Course    : {app.course.fullname}\n"
        f"Department: {app.department}\n"
        f"Employee  : {app.employee_id or 'N/A'}\n\n"
        f"Log in to the ILMP admin portal to review this application."
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
    except Exception as exc:
        logger.exception("notify_application_submitted: send failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def notify_application_reviewed(self, application_id):
    from .models import Application, ApplicationStatus

    try:
        app = Application.objects.select_related("applicant", "course").get(id=application_id)
    except Application.DoesNotExist:
        logger.error("notify_application_reviewed: application %s not found", application_id)
        return

    templates = {
        ApplicationStatus.APPROVED: (
            f"Application approved: {app.course.fullname}",
            (
                f"Congratulations, {app.applicant.first_name}!\n\n"
                f"Your application for {app.course.fullname} has been approved.\n\n"
                f"Next step: You will receive a payment link shortly."
            ),
        ),
        ApplicationStatus.REJECTED: (
            f"Application outcome: {app.course.fullname}",
            (
                f"Hi {app.applicant.first_name},\n\n"
                f"Unfortunately your application for {app.course.fullname} was not approved.\n\n"
                f"Reason: {app.rejection_reason or 'No reason provided.'}\n\n"
                f"Contact your reviewer for further information."
            ),
        ),
        ApplicationStatus.MORE_INFO_REQUESTED: (
            f"Additional information required: {app.course.fullname}",
            (
                f"Hi {app.applicant.first_name},\n\n"
                f"Your reviewer has requested additional information.\n\n"
                f"Request: {app.more_info_request}\n\n"
                f"Please log in to the ILMP portal, update your application, and resubmit."
            ),
        ),
    }

    subject, message = templates.get(
        app.status,
        (
            f"Update on your application: {app.course.fullname}",
            f"Your application status has been updated to: {app.get_status_display()}",
        ),
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [app.applicant.email])
    except Exception as exc:
        logger.exception("notify_application_reviewed: send failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def notify_payment_required(self, application_id):
    from .models import Application

    try:
        app = Application.objects.select_related("applicant", "course").get(id=application_id)
    except Application.DoesNotExist:
        logger.error("notify_payment_required: application %s not found", application_id)
        return

    price = app.course.price or "N/A"
    subject = f"Payment required: {app.course.fullname}"
    message = (
        f"Hi {app.applicant.first_name},\n\n"
        f"Your application for {app.course.fullname} is approved and awaiting payment.\n\n"
        f"Course fee : {price} USD\n\n"
        f"Log in to the ILMP portal and go to My Applications to complete payment via Paynow.\n"
        f"Enrolment is activated automatically once payment is confirmed."
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [app.applicant.email])
    except Exception as exc:
        logger.exception("notify_payment_required: send failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def notify_enrolled(self, application_id):
    from .models import Application

    try:
        app = Application.objects.select_related("applicant", "course").get(id=application_id)
    except Application.DoesNotExist:
        logger.error("notify_enrolled: application %s not found", application_id)
        return

    moodle_url = getattr(settings, "MOODLE_BASE_URL", "")
    subject = f"Welcome to {app.course.fullname}!"
    message = (
        f"Congratulations, {app.applicant.first_name}!\n\n"
        f"You have been successfully enrolled in {app.course.fullname}.\n\n"
        f"Access your course: {moodle_url}\n\n"
        f"If you have questions, contact the ZESA training department."
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [app.applicant.email])
    except Exception as exc:
        logger.exception("notify_enrolled: send failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
