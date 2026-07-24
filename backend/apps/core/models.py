import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    FRS §3.5 / §6.1: field-level audit trail for selected tables, plus user
    creation/deletion and login/logout. Deliberately separate from
    applications.ApplicationStatusHistory, which already covers Application
    status transitions with its own actor/EC-number snapshotting — this
    model covers what that one doesn't: User lifecycle, Certificate
    revocation, and Enrollment suspension.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Created"
        UPDATE = "UPDATE", "Updated"
        DELETE = "DELETE", "Deleted"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    actor_email = models.EmailField(blank=True, default="")
    actor_ec_number = models.CharField(max_length=20, blank=True, default="")
    action = models.CharField(max_length=10, choices=Action.choices)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=300, blank=True)
    field_name = models.CharField(
        max_length=100, blank=True,
        help_text="Which field changed (blank for CREATE/DELETE/LOGIN/LOGOUT)",
    )
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["actor", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return (
            f"{self.timestamp:%Y-%m-%d %H:%M} | "
            f"{self.actor_email or 'System'} | {self.action} | {self.model_name}"
        )

    @classmethod
    def log(cls, actor, action, instance, field_name="",
            old_value="", new_value="", request=None, notes=""):
        ip = None
        ua = ""
        if request is not None:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for \
                else request.META.get("REMOTE_ADDR")
            ua = request.META.get("HTTP_USER_AGENT", "")[:500]

        return cls.objects.create(
            actor=actor,
            actor_email=actor.email if actor else "",
            actor_ec_number=getattr(actor, "ec_number", "") if actor else "",
            action=action,
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            object_repr=str(instance)[:300],
            field_name=field_name,
            old_value=str(old_value)[:2000] if old_value != "" else "",
            new_value=str(new_value)[:2000] if new_value != "" else "",
            ip_address=ip,
            user_agent=ua,
            notes=notes,
        )
