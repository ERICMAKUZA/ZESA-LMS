from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source="generated_by.full_name", read_only=True)

    class Meta:
        model = Report
        fields = (
            "id", "title", "report_type", "generated_by", "generated_by_name",
            "parameters", "file_url", "generated_at",
        )
        read_only_fields = ("id", "generated_by", "generated_at")
