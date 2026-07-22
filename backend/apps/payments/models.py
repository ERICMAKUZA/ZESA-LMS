import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class PaymentMethod(models.TextChoices):
    PAYNOW = "PAYNOW", "Paynow"
    SAP_BUDGET = "SAP_BUDGET", "SAP Budget Transfer"
    CASH = "CASH", "Cash"
    EFT = "EFT", "EFT / Bank Transfer"
    RTGS = "RTGS", "RTGS"
    ECOCASH = "ECOCASH", "EcoCash"
    ZIMSWITCH = "ZIMSWITCH", "ZimSwitch"
    COMPANY = "COMPANY", "Company / Sponsor Payment"

    @classmethod
    def manual_methods(cls):
        return (cls.CASH, cls.EFT, cls.RTGS, cls.ECOCASH, cls.ZIMSWITCH, cls.COMPANY)


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
    reference = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Bank reference, EcoCash transaction ID, or receipt number "
                   "(manually confirmed payments)."
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="payment_confirmations",
        help_text="Staff member who manually confirmed this payment, if applicable.",
    )
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

    def confirm_manual(self, confirmed_by, method, reference):
        """
        Admin/Finance-driven manual payment confirmation — bridges the gap
        while SAP/PayNow integration is deferred.
        """
        if self.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            raise ValueError(
                f"Cannot confirm payment: payment is {self.status}, "
                f"expected PENDING or PROCESSING"
            )
        self.method = method
        self.reference = reference
        self.confirmed_by = confirmed_by
        self.status = PaymentStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save(update_fields=[
            "method", "reference", "confirmed_by", "status", "confirmed_at",
        ])
        self.application.confirm_payment()

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
