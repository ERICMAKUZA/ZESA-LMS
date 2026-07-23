from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin

from .models import Certificate
from .serializers import CertificatePublicSerializer, CertificateSerializer


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
            cert = Certificate.objects.select_related(
                "user", "course", "enrollment__application__assigned_centre",
            ).get(certificate_number=certificate_number)
        except Certificate.DoesNotExist:
            return Response({
                "valid": False,
                "detail": (
                    f"No certificate found with number '{certificate_number}'. "
                    f"If you believe this is an error, contact ZNTC at training@zntc.ac.zw."
                ),
            }, status=404)

        return Response(CertificatePublicSerializer(cert).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def revoke(self, request, pk=None):
        cert = self.get_object()
        reason = (request.data.get("reason") or "").strip()
        if not reason:
            return Response({"detail": "Revocation reason is required."}, status=400)

        try:
            cert.revoke(revoked_by=request.user, reason=reason)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(CertificateSerializer(cert, context={"request": request}).data)
