import logging

from django.db import transaction
from django.utils import timezone

from .models import Notification
from .tasks import send_notification
from .templates import render_acceptance, render_calendar_event, render_certificate_collection

logger = logging.getLogger(__name__)


def queue_notification(
    *,
    recipient,
    subject,
    message,
    application=None,
    action_url="",
    channel=Notification.Channel.EMAIL,
    dispatch=True,
):
    notification = Notification.objects.create(
        recipient=recipient,
        application=application,
        subject=subject,
        message=message,
        action_url=action_url,
        channel=channel,
    )

    if dispatch and recipient and recipient.email:
        transaction.on_commit(lambda: _dispatch_notification(notification.id))

    return notification


def queue_notifications(
    *,
    recipients,
    subject,
    message,
    application=None,
    action_url="",
    dispatch=True,
):
    notifications = []
    seen = set()
    for recipient in recipients:
        if not recipient or recipient.id in seen:
            continue
        seen.add(recipient.id)
        notifications.append(
            queue_notification(
                recipient=recipient,
                subject=subject,
                message=message,
                application=application,
                action_url=action_url,
                dispatch=dispatch,
            )
        )
    return notifications


def staff_recipients(*roles):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.filter(role__in=roles, is_active=True)


def queue_acceptance_notification(application):
    schedule = next(
        (
            intake for intake in application.course.schedules.filter(status="OPEN")
            if intake.get_approximate_start_date() >= timezone.localdate()
        ),
        None,
    )
    subject, message = render_acceptance(application, schedule)
    return queue_notification(
        recipient=application.applicant,
        subject=subject,
        message=message,
        application=application,
        action_url=f"/applications/{application.id}",
    )


def queue_certificate_collection_notification(certificate):
    subject, message = render_certificate_collection(certificate)
    return queue_notification(
        recipient=certificate.user,
        subject=subject,
        message=message,
        application=certificate.enrollment.application,
        action_url="/certificates",
    )


def publish_calendar_event(event):
    from django.contrib.auth import get_user_model
    from django.db.models import Q

    from apps.applications.models import ApplicationStatus
    from apps.enrollments.models import Enrollment, EnrollmentStatus

    User = get_user_model()
    student_enrollments = Enrollment.objects.filter(
        application__status=ApplicationStatus.ENROLLED
    ).exclude(status=EnrollmentStatus.UNENROLLED)
    if event.schedule_id:
        student_enrollments = student_enrollments.filter(schedule_id=event.schedule_id)
    elif event.course_id:
        student_enrollments = student_enrollments.filter(application__course_id=event.course_id)

    if event.event_type == "COMMENCEMENT":
        action_url = "/dashboard/learning"
    elif event.event_type == "EXAMINATION":
        action_url = event.timetable_url
    else:
        action_url = f"/courses/{event.course_id}" if event.course_id else "/courses"
    notifications = []
    if event.audience in ("STUDENTS", "BOTH"):
        students = User.objects.filter(
            pk__in=student_enrollments.values("application__applicant_id"),
            is_active=True,
        )
        subject, message = render_calendar_event(event, "STUDENT")
        notifications.extend(queue_notifications(
            recipients=students, subject=subject, message=message, action_url=action_url,
        ))

    if event.audience in ("LECTURERS", "BOTH"):
        lecturers = User.objects.filter(role=User.Role.LECTURER, is_active=True)
        if event.course_id:
            lecturers = lecturers.filter(
                Q(assigned_courses__id=event.course_id)
                | Q(assigned_schedules__course_id=event.course_id)
            ).distinct()
        subject, message = render_calendar_event(event, "LECTURER")
        notifications.extend(queue_notifications(
            recipients=lecturers, subject=subject, message=message, action_url=action_url,
        ))
    return notifications


def _dispatch_notification(notification_id):
    try:
        send_notification.delay(notification_id)
    except Exception as exc:
        Notification.objects.filter(pk=notification_id).update(
            error_message=f"Could not enqueue email: {exc}"
        )
        logger.warning(
            "Could not enqueue email notification %s: %s",
            notification_id,
            exc,
        )
