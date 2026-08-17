import logging

from django.db import transaction

from .models import Notification
from .tasks import send_notification

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


def _dispatch_notification(notification_id):
    try:
        send_notification.delay(notification_id)
    except Exception as exc:
        logger.warning(
            "Could not enqueue email notification %s: %s",
            notification_id,
            exc,
        )
