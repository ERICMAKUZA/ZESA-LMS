from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.EMAIL)
    action_url = models.CharField(max_length=500, blank=True, default="")
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.channel}] {self.subject} → {self.recipient.email}"

    def mark_read(self):
        from django.utils import timezone

        if self.is_read:
            return
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])


class ApprovalStep(models.Model):
    class Action(models.TextChoices):
        APPROVE = "APPROVE", "Approve"
        REJECT = "REJECT", "Reject"
        ESCALATE = "ESCALATE", "Escalate"
        REQUEST_INFO = "REQUEST_INFO", "Request Info"

    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="workflow_steps",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reviewed_steps",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    comment = models.TextField(blank=True)
    step_order = models.PositiveSmallIntegerField(default=1)
    acted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Approval Step"
        verbose_name_plural = "Approval Steps"
        ordering = ["application", "step_order", "acted_at"]

    def __str__(self):
        return f"Step {self.step_order} on application #{self.application_id} – {self.action}"
