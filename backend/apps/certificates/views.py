from rest_framework import permissions, viewsets

from apps.accounts.models import User

from .models import Certificate
from .serializers import CertificateSerializer


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["course"]
    ordering_fields = ["issued_at"]
    queryset = Certificate.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Certificate.objects.none()
        user = self.request.user
        if user.role in (User.Role.ADMIN, User.Role.SUPERADMIN):
            return Certificate.objects.all().select_related("user", "course")
        return Certificate.objects.filter(user=user).select_related("course")
