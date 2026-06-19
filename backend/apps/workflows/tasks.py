import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_notification(self, notification_id):
    from .models import Notification

    try:
        notification = Notification.objects.select_related("recipient").get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error("send_notification: notification %s not found", notification_id)
        return

    try:
        send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
        )
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.error_message = ""
        notification.save(update_fields=["is_sent", "sent_at", "error_message"])
    except Exception as exc:
        logger.exception("send_notification: failed for notification %s: %s", notification_id, exc)
        notification.error_message = str(exc)
        notification.save(update_fields=["error_message"])
        raise self.retry(exc=exc, countdown=60)
