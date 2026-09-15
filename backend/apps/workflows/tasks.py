import logging
import re

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def _next_quarter_key(today):
    quarter = (today.month - 1) // 3 + 2
    return f"{today.year + (quarter > 4)}-Q{1 if quarter > 4 else quarter}"


@shared_task(name="workflows.broadcast_upcoming_courses")
def broadcast_upcoming_courses(quarter_key=None):
    from django.contrib.auth import get_user_model
    from django.db import transaction

    from apps.courses.models import CourseSchedule
    from .models import Notification
    from .services import queue_notification
    from .templates import render_upcoming_courses

    quarter_key = quarter_key or _next_quarter_key(timezone.localdate())
    match = re.fullmatch(r"(\d{4})-Q([1-4])", quarter_key)
    if not match:
        raise ValueError("quarter_key must use YYYY-Q1 through YYYY-Q4")
    year, quarter = map(int, match.groups())
    first_month = (quarter - 1) * 3 + 1
    schedules = list(
        CourseSchedule.objects.select_related("course").filter(
            year=year, month__gte=first_month, month__lte=first_month + 2,
            status="OPEN", course__is_active=True, course__course_type__is_active=True,
            course__course_type__code__in=("HEXCO", "UZ"),
        ).order_by("year", "month", "week_in_month", "course__fullname")
    )
    if not schedules:
        return 0

    subject, message = render_upcoming_courses(quarter_key, schedules)
    User = get_user_model()
    sent = 0
    for user_id in User.objects.filter(role=User.Role.STUDENT, is_active=True).values_list("id", flat=True):
        with transaction.atomic():
            recipient = User.objects.select_for_update().get(pk=user_id)
            if Notification.objects.filter(recipient=recipient, subject=subject).exists():
                continue
            queue_notification(
                recipient=recipient, subject=subject, message=message, action_url="/courses",
            )
            sent += 1
    return sent


@shared_task(bind=True, max_retries=3)
def send_notification(self, notification_id):
    from .models import Notification

    try:
        notification = Notification.objects.select_related("recipient").get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error("send_notification: notification %s not found", notification_id)
        return

    try:
        delivered = send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
        )
        if delivered != 1:
            raise RuntimeError("Email backend delivered to zero recipients")
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.error_message = ""
        notification.save(update_fields=["is_sent", "sent_at", "error_message"])
    except Exception as exc:
        logger.exception("send_notification: failed for notification %s: %s", notification_id, exc)
        notification.error_message = str(exc)
        notification.save(update_fields=["error_message"])
        raise self.retry(exc=exc, countdown=60)
