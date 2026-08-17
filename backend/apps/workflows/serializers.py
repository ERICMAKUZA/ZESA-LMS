from rest_framework import serializers

from .models import ApprovalStep, Notification


class NotificationSerializer(serializers.ModelSerializer):
    application_ref = serializers.CharField(source="application.ref", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id", "recipient", "application", "application_ref",
            "subject", "message", "channel", "action_url",
            "is_sent", "sent_at", "error_message",
            "is_read", "read_at", "created_at",
        )
        read_only_fields = fields


class ApprovalStepSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.full_name", read_only=True)

    class Meta:
        model = ApprovalStep
        fields = (
            "id", "application", "reviewer", "reviewer_name",
            "action", "comment", "step_order", "acted_at",
        )
        read_only_fields = ("id", "reviewer", "acted_at")
