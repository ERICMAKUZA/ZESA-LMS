from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrReviewer

from .models import ApprovalStep, Notification
from .serializers import ApprovalStepSerializer, NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "application"
        )

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_read()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return Response({"updated": updated}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        return Response({"count": self.get_queryset().filter(is_read=False).count()})


class ApprovalStepViewSet(viewsets.ModelViewSet):
    queryset = ApprovalStep.objects.all().select_related("application", "reviewer")
    serializer_class = ApprovalStepSerializer
    permission_classes = [IsAdminOrReviewer]
    filterset_fields = ["application", "action"]
    ordering_fields = ["acted_at", "step_order"]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
