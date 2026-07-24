from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = (
            "id", "timestamp", "actor_email", "actor_ec_number",
            "action", "model_name", "object_id", "object_repr",
            "field_name", "old_value", "new_value",
            "ip_address", "notes",
        )
        read_only_fields = fields
