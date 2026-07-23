from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import User

from .models import Certificate
from .serializers import CertificateSerializer


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["course"]
    ordering_fields = ["issued_at"]
    queryset = Certificate.objects.none()

    def get_permissions(self):
        if self.action == "verify":
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Certificate.objects.none()
        user = self.request.user
        if user.role in (User.Role.ADMIN, User.Role.SUPERADMIN):
            return Certificate.objects.all().select_related("user", "course")
        return Certificate.objects.filter(user=user).select_related("course")

    @action(detail=False, methods=["get"], url_path=r"verify/(?P<certificate_number>[^/.]+)")
    def verify(self, request, certificate_number=None):
        try:
            cert = Certificate.objects.select_related("user", "course").get(
                certificate_number=certificate_number
            )
        except Certificate.DoesNotExist:
            return Response({"detail": "Certificate not found."}, status=404)

        return Response({
            "valid": not cert.is_revoked,
            "holder_name": cert.user.full_name,
            "course": cert.course.fullname,
            "issued_at": cert.issued_at,
            "status": cert.status_display,
        })
