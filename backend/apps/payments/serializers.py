from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "application",
            "amount",
            "currency",
            "method",
            "status",
            "paynow_reference",
            "paynow_poll_url",
            "paynow_redirect_url",
            "sap_document_number",
            "sap_cost_center",
            "initiated_at",
            "confirmed_at",
            "failed_reason",
        )
        read_only_fields = fields


class InitiatePaymentSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()

    def validate_application_id(self, value):
        from apps.applications.models import Application, ApplicationStatus

        request = self.context.get("request")
        try:
            application = Application.objects.select_related("course").get(
                id=value,
                applicant=request.user,
            )
        except Application.DoesNotExist:
            raise serializers.ValidationError("Application not found.")

        if application.status != ApplicationStatus.APPROVED:
            raise serializers.ValidationError(
                f"Application must be APPROVED to initiate payment (current: {application.status})."
            )

        if not application.course.price:
            raise serializers.ValidationError("This course has no price set.")

        if hasattr(application, "payment"):
            existing = application.payment
            if existing.status not in ("FAILED",):
                raise serializers.ValidationError("A payment already exists for this application.")

        return value
