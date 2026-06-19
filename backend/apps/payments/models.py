import uuid

from django.db import models
from django.utils import timezone


class PaymentMethod(models.TextChoices):
    PAYNOW = "PAYNOW", "Paynow"
    SAP_BUDGET = "SAP_BUDGET", "SAP Budget Transfer"
    MANUAL = "MANUAL", "Manual"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    CONFIRMED = "CONFIRMED", "Confirmed"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="payment",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    paynow_reference = models.CharField(max_length=255, blank=True, null=True)
    paynow_poll_url = models.CharField(max_length=500, blank=True, null=True)
    paynow_redirect_url = models.CharField(max_length=500, blank=True, null=True)
    sap_document_number = models.CharField(max_length=100, blank=True, null=True)
    sap_cost_center = models.CharField(max_length=100, blank=True, null=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.CharField(max_length=500, blank=True, null=True)
    raw_webhook_payload = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-initiated_at"]

    def __str__(self):
        return f"Payment {self.id} - {self.application} - {self.status}"

    def confirm(self):
        self.status = PaymentStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save(update_fields=["status", "confirmed_at"])
        self.application.confirm_payment()
        self.application.save()

    def fail(self, reason: str):
        self.status = PaymentStatus.FAILED
        self.failed_reason = reason
        self.save(update_fields=["status", "failed_reason"])


class SAPSyncLog(models.Model):
    synced_at = models.DateTimeField(auto_now_add=True)
    records_processed = models.IntegerField(default=0)
    records_matched = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    success = models.BooleanField(default=True)

    class Meta:
        verbose_name = "SAP Sync Log"
        verbose_name_plural = "SAP Sync Logs"
        ordering = ["-synced_at"]

    def __str__(self):
        return f"SAP Sync {self.synced_at:%Y-%m-%d %H:%M} — processed={self.records_processed} matched={self.records_matched}"
