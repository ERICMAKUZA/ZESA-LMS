import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)


def _student_application_url(app):
    return f"/applications/{app.id}"


def _admin_application_url(app):
    return f"/admin/applications/{app.id}"


@shared_task(bind=True, max_retries=3)
def notify_application_submitted(self, application_id):
    from .models import Application

    try:
        app = Application.objects.select_related("applicant", "course").get(id=application_id)
    except Application.DoesNotExist:
        logger.error("notify_application_submitted: application %s not found", application_id)
        return

    from apps.workflows.services import queue_notification, queue_notifications, staff_recipients

    reviewers = staff_recipients("REVIEWER", "ADMIN", "SUPERADMIN")
    if not reviewers.exists():
        logger.warning("notify_application_submitted: no reviewer/admin users found")

    subject = f"New application: {app.applicant.full_name} for {app.course.fullname}"
    message = (
        f"A new training application has been submitted.\n\n"
        f"Applicant : {app.applicant.full_name} ({app.applicant.email})\n"
        f"Course    : {app.course.fullname}\n"
        f"Department: {app.department}\n"
        f"Employee  : {app.employee_id or 'N/A'}\n\n"
        f"Log in to the NTC admin portal to review this application."
    )
    queue_notifications(
        recipients=reviewers,
        subject=subject,
        message=message,
        application=app,
        action_url=_admin_application_url(app),
    )
    queue_notification(
        recipient=app.applicant,
        subject=f"Application submitted: {app.course.fullname}",
        message=(
            f"Hi {app.applicant.first_name},\n\n"
            f"We received your application for {app.course.fullname}.\n\n"
            "The admissions team will review it and you will be notified at each stage."
        ),
        application=app,
        action_url=_student_application_url(app),
    )


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
                f"Please log in to the NTC portal, update your application, and resubmit."
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

    from apps.workflows.services import queue_notification

    queue_notification(
        recipient=app.applicant,
        subject=subject,
        message=message,
        application=app,
        action_url=_student_application_url(app),
    )


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
        f"Log in to the NTC portal and go to My Applications to complete payment via Paynow.\n"
        f"Enrolment is activated automatically once payment is confirmed."
    )
    from apps.workflows.services import queue_notification

    queue_notification(
        recipient=app.applicant,
        subject=subject,
        message=message,
        application=app,
        action_url=_student_application_url(app),
    )


@shared_task(name='applications.escalate_stale_applications')
def escalate_stale_applications():
    from datetime import timedelta
    from .models import Application
    threshold_days = getattr(settings, 'ESCALATION_DAYS_THRESHOLD', 3)
    cutoff = timezone.now() - timedelta(days=threshold_days)
    stale = Application.objects.filter(
        status__in=['SUBMITTED', 'UNDER_REVIEW'],
        escalated=False,
        updated_at__lt=cutoff,
    )
    escalated_count = 0
    for app in stale:
        app.escalated = True
        app.escalated_at = timezone.now()
        app.save(update_fields=['escalated', 'escalated_at'])
        notify_escalation.delay(str(app.pk))
        escalated_count += 1
    return f"Escalated {escalated_count} applications"


@shared_task(name='applications.notify_escalation')
def notify_escalation(application_pk):
    from .models import Application
    try:
        app = Application.objects.select_related('course', 'reviewer').get(pk=application_pk)
    except Application.DoesNotExist:
        return
    User = get_user_model()
    if app.reviewer:
        recipients = [app.reviewer]
    else:
        recipients = User.objects.filter(
            role__in=['REVIEWER', 'ADMIN', 'SUPERADMIN'],
            is_active=True,
        )
    if not recipients:
        return
    threshold_days = getattr(settings, 'ESCALATION_DAYS_THRESHOLD', 3)
    from apps.workflows.services import queue_notifications

    queue_notifications(
        recipients=recipients,
        subject=f"[ESCALATED] Application {app.ref} needs attention",
        message=(
            f"Application {app.ref} for "
            f"{app.course.fullname if app.course else 'N/A'} "
            f"has been waiting for review for more than {threshold_days} days.\n\n"
            f"Please review it at your earliest convenience."
        ),
        application=app,
        action_url=_admin_application_url(app),
    )


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
    from apps.workflows.services import queue_notification

    queue_notification(
        recipient=app.applicant,
        subject=subject,
        message=message,
        application=app,
        action_url="/dashboard",
    )
