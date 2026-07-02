import logging

from django.conf import settings
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin
from apps.applications.models import Application

from .models import Enrollment, EnrollmentStatus
from .serializers import EnrollmentListSerializer, EnrollmentSerializer, StudentEnrollmentSerializer
from .services import MoodleAPIError, MoodleEnrollmentService

logger = logging.getLogger(__name__)


class StudentEnrollmentListView(generics.ListAPIView):
    serializer_class = StudentEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return (
            Enrollment.objects.filter(application__applicant=self.request.user)
            .select_related("application__course")
            .order_by("-enrolled_at")
        )


class EnrollmentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, application_id):
        try:
            enrollment = Enrollment.objects.select_related(
                "application__applicant", "application__course"
            ).get(application_id=application_id)
        except Enrollment.DoesNotExist:
            return Response({"detail": "Enrollment not found."}, status=status.HTTP_404_NOT_FOUND)

        if enrollment.application.applicant != request.user:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        moodle_url = None
        if enrollment.moodle_course_id:
            base = getattr(settings, "MOODLE_BASE_URL", "").rstrip("/")
            moodle_url = f"{base}/course/view.php?id={enrollment.moodle_course_id}"

        return Response({
            "id": str(enrollment.id),
            "status": enrollment.status,
            "enrolled_at": enrollment.enrolled_at,
            "moodle_course_id": enrollment.moodle_course_id,
            "moodle_course_url": moodle_url,
            "error_message": enrollment.error_message,
        })


class AdminEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    filterset_fields = ["status", "application__course"]

    def get_queryset(self):
        return (
            Enrollment.objects.all()
            .select_related("application__applicant", "application__course")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EnrollmentSerializer
        return EnrollmentListSerializer

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.status != EnrollmentStatus.FAILED:
            return Response(
                {"detail": f"Can only retry FAILED enrollments (current: {enrollment.status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .tasks import enroll_student_in_moodle
        enroll_student_in_moodle.apply_async([str(enrollment.application_id)])
        return Response({"detail": "Enrollment retry queued."})

    @action(detail=True, methods=["post"])
    def unenroll(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.status != EnrollmentStatus.ENROLLED:
            return Response(
                {"detail": f"Can only unenroll ENROLLED students (current: {enrollment.status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not enrollment.moodle_user_id:
            return Response(
                {"detail": "No Moodle user ID on record."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        svc = MoodleEnrollmentService()
        try:
            svc.unenroll_user(enrollment.moodle_user_id, enrollment.moodle_course_id)
        except MoodleAPIError as exc:
            logger.error("unenroll action failed for enrollment %s: %s", pk, exc)
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        from django.utils import timezone
        enrollment.status = EnrollmentStatus.UNENROLLED
        enrollment.unenrolled_at = timezone.now()
        enrollment.save(update_fields=["status", "unenrolled_at"])
        return Response(EnrollmentSerializer(enrollment, context={"request": request}).data)
