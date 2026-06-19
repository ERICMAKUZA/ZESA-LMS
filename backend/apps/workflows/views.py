from rest_framework import viewsets

from apps.accounts.permissions import IsAdminOrReviewer

from .models import ApprovalStep
from .serializers import ApprovalStepSerializer


class ApprovalStepViewSet(viewsets.ModelViewSet):
    queryset = ApprovalStep.objects.all().select_related("application", "reviewer")
    serializer_class = ApprovalStepSerializer
    permission_classes = [IsAdminOrReviewer]
    filterset_fields = ["application", "action"]
    ordering_fields = ["acted_at", "step_order"]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
