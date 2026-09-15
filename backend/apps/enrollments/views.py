import csv
import logging
from collections.abc import Mapping

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin, IsAdminOrReviewerOrCentreAdmin
from apps.applications.models import Application, ApplicationStatus
from apps.courses.models import CourseSchedule
from apps.workflows.services import queue_notification

from .models import Enrollment, EnrollmentAttendanceResponse, EnrollmentStatus
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
            .select_related("application__course", "attendance_response")
            .order_by("-enrolled_at")
        )

    def list(self, request, *args, **kwargs):
        enrollments = list(self.get_queryset())
        data = list(self.get_serializer(enrollments, many=True).data)
        for item, enrollment in zip(data, enrollments):
            attendance = getattr(enrollment, "attendance_response", None)
            item["attendance_response"] = _attendance_response_data(attendance) if attendance else None
        return Response(data)


def _attendance_response_data(attendance):
    return {
        "response": attendance.response,
        "responded_at": attendance.responded_at,
        "target_schedule": str(attendance.target_schedule_id) if attendance.target_schedule_id else None,
        "audit_note": attendance.audit_note,
    }


class EnrollmentAttendanceResponseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, enrollment_id):
        requested = request.data.get("response") if isinstance(request.data, Mapping) else None
        if requested not in ("CONFIRMED", "DEFER"):
            return Response(
                {"detail": "response must be CONFIRMED or DEFER."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            enrollment = (
                Enrollment.objects.select_for_update()
                .select_related("application__course", "application__applicant")
                .filter(pk=enrollment_id, application__applicant=request.user)
                .first()
            )
            if enrollment is None:
                raise NotFound("Enrollment not found.")
            if enrollment.status == EnrollmentStatus.UNENROLLED or enrollment.is_suspended:
                return Response(
                    {"detail": "Attendance response is unavailable for this enrollment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if EnrollmentAttendanceResponse.objects.filter(enrollment=enrollment).exists():
                return Response(
                    {"detail": "Attendance response has already been submitted."},
                    status=status.HTTP_409_CONFLICT,
                )

            target = None
            response_status = EnrollmentAttendanceResponse.Response.CONFIRMED
            audit_note = "Student confirmed attendance."
            if requested == "DEFER":
                response_status = EnrollmentAttendanceResponse.Response.PENDING_STAFF
                audit_note = "No later open intake with capacity; staff review required."
                if enrollment.schedule_id:
                    current = CourseSchedule.objects.select_for_update().get(pk=enrollment.schedule_id)
                    cutoff = max(timezone.localdate(), current.get_approximate_start_date())
                    candidates = (
                        CourseSchedule.objects.select_for_update()
                        .filter(course_id=enrollment.application.course_id, status="OPEN", year__gte=current.year)
                        .order_by("year", "month", "week_in_month")
                    )
                    for candidate in candidates:
                        if candidate.pk == current.pk or candidate.get_approximate_start_date() <= cutoff:
                            continue
                        actual_occupied = Enrollment.objects.filter(schedule=candidate).exclude(
                            status=EnrollmentStatus.UNENROLLED,
                        ).count()
                        occupied = max(candidate.enrolled_count, actual_occupied)
                        if occupied >= candidate.max_capacity:
                            continue
                        reserved = CourseSchedule.objects.filter(
                            pk=candidate.pk, status="OPEN",
                            enrolled_count__lte=occupied, max_capacity__gt=occupied,
                        ).update(enrolled_count=occupied + 1)
                        if not reserved:
                            continue
                        source_occupied = Enrollment.objects.filter(schedule=current).exclude(
                            status=EnrollmentStatus.UNENROLLED,
                        ).count()
                        CourseSchedule.objects.filter(pk=current.pk).update(
                            enrolled_count=max(0, source_occupied - 1),
                        )
                        target = candidate
                        enrollment.schedule = target
                        enrollment.start_date = target.get_approximate_start_date()
                        enrollment.end_date = (
                            target.get_approximate_end_date()
                            if enrollment.application.course.duration_days else None
                        )
                        enrollment.save(update_fields=["schedule", "start_date", "end_date"])
                        response_status = EnrollmentAttendanceResponse.Response.DEFERRED
                        audit_note = f"Transferred from intake {current.pk} to {target.pk}."
                        break

            attendance = EnrollmentAttendanceResponse.objects.create(
                enrollment=enrollment, response=response_status,
                target_schedule=target, audit_note=audit_note,
            )
            course_name = enrollment.application.course.fullname
            if response_status == EnrollmentAttendanceResponse.Response.CONFIRMED:
                message = f"Your attendance for {course_name} has been confirmed."
            elif response_status == EnrollmentAttendanceResponse.Response.DEFERRED:
                message = (
                    f"Your deferral for {course_name} has been accepted. "
                    f"Your new intake starts on {enrollment.start_date:%d %B %Y}."
                )
            else:
                message = (
                    f"Your deferral request for {course_name} is pending staff review. "
                    "No later intake with space is currently available."
                )
            queue_notification(
                recipient=request.user,
                application=enrollment.application,
                subject=f"Attendance response: {course_name}",
                message=message,
                action_url="/dashboard/learning",
            )

        return Response(_attendance_response_data(attendance))


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
    filterset_fields = [
        "status", "application__status", "application__course",
        "application__assigned_centre", "application__department",
    ]
    search_fields = [
        "application__applicant__first_name",
        "application__applicant__last_name",
        "application__applicant__student_id",
        "application__ref",
    ]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAdminOrReviewerOrCentreAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        return (
            Enrollment.objects.all()
            .select_related(
                "application__applicant", "application__course",
                "application__assigned_centre", "application__payment",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EnrollmentSerializer
        return EnrollmentListSerializer

    @action(detail=False, methods=["get"])
    def export(self, request):
        """GET /api/admin/enrollments/export/ — CSV of enrolled students, Admin only."""
        qs = self.filter_queryset(
            self.get_queryset().filter(application__status=ApplicationStatus.ENROLLED)
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="zntc_enrolled_students_{timezone.now():%Y%m%d_%H%M}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow([
            "Student ID", "First Name", "Last Name", "ZNTC Email",
            "Personal Email", "Phone", "Course", "Programme Level",
            "Department", "Centre", "Payment Method", "Payment Reference",
            "Payment Amount (USD)", "Payment Confirmed At",
            "Moodle Sync Status", "Enrolled At", "Application Ref",
        ])
        for enrollment in qs:
            app = enrollment.application
            applicant = app.applicant
            payment = getattr(app, "payment", None)
            writer.writerow([
                applicant.student_id or "",
                applicant.first_name,
                applicant.last_name,
                applicant.zntc_email or "",
                applicant.email,
                applicant.phone,
                app.course.fullname if app.course else "",
                app.hexco_level or "Short Course",
                app.department,
                app.assigned_centre.name if app.assigned_centre else "",
                payment.method if payment else "",
                payment.reference if payment else "",
                str(payment.amount) if payment else "",
                payment.confirmed_at.strftime("%Y-%m-%d %H:%M") if payment and payment.confirmed_at else "",
                enrollment.status,
                enrollment.enrolled_at.strftime("%Y-%m-%d %H:%M") if enrollment.enrolled_at else "",
                app.ref,
            ])
        return response

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
    def issue_certificate(self, request, pk=None):
        enrollment = self.get_object()
        from apps.certificates.models import Certificate

        try:
            cert = Certificate.issue_from_enrollment(enrollment, issued_by=request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from apps.certificates.serializers import CertificateSerializer
        return Response(
            CertificateSerializer(cert, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        enrollment = self.get_object()
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response({"detail": "reason is required."}, status=status.HTTP_400_BAD_REQUEST)
        if enrollment.is_suspended:
            return Response({"detail": "Enrollment is already suspended."}, status=status.HTTP_400_BAD_REQUEST)
        enrollment._audit_actor = request.user
        enrollment.suspend(reason)
        return Response(EnrollmentSerializer(enrollment, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def reinstate(self, request, pk=None):
        enrollment = self.get_object()
        if not enrollment.is_suspended:
            return Response({"detail": "Enrollment is not suspended."}, status=status.HTTP_400_BAD_REQUEST)
        enrollment._audit_actor = request.user
        enrollment.reinstate()
        return Response(EnrollmentSerializer(enrollment, context={"request": request}).data)

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
