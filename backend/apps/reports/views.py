from rest_framework import viewsets

from apps.accounts.permissions import IsAdmin

from .models import Report
from .serializers import ReportSerializer


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().select_related("generated_by")
    serializer_class = ReportSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["report_type"]
    search_fields = ["title"]
    ordering_fields = ["generated_at", "title", "report_type"]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)
