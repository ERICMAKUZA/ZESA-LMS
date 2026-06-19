from rest_framework import serializers

from .models import ApprovalStep


class ApprovalStepSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.full_name", read_only=True)

    class Meta:
        model = ApprovalStep
        fields = (
            "id", "application", "reviewer", "reviewer_name",
            "action", "comment", "step_order", "acted_at",
        )
        read_only_fields = ("id", "reviewer", "acted_at")
