from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework import status as http_status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsAdminOrReviewer, IsLecturer
from apps.enrollments.models import Enrollment

from .filters import ApplicationFilter
from .models import Application, ApplicationStatus
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationDetailSerializer,
    ApplicationListSerializer,
    LecturerApplicationSerializer,
    ReviewActionSerializer,
)
from .tasks import (
    notify_application_reviewed,
    notify_application_submitted,
    notify_payment_required,
)


class StudentApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Application.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Application.objects.none()
        return (
            Application.objects.filter(applicant=self.request.user)
            .select_related("course", "reviewer")
            .prefetch_related("documents", "history")
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ApplicationCreateSerializer
        if self.action == "retrieve":
            return ApplicationDetailSerializer
        return ApplicationListSerializer

    def perform_create(self, serializer):
        if serializer.validated_data.get('source') == 'WALK_IN':
            serializer.save(staff_captured_by=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        application = self.get_object()
        try:
            application.submit()
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        notify_application_submitted.delay(str(application.id))
        return Response(ApplicationDetailSerializer(application, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="provide_info")
    def provide_info(self, request, pk=None):
        application = self.get_object()
        try:
            application.submit()
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        notify_application_submitted.delay(str(application.id))
        return Response(ApplicationDetailSerializer(application, context={"request": request}).data)


class AdminApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReviewer]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_class = ApplicationFilter
    ordering_fields = ["created_at", "submitted_at", "status", "approved_at"]

    def get_queryset(self):
        return (
            Application.objects.all()
            .select_related("applicant", "course", "reviewer", "enrollment", "payment")
            .prefetch_related("documents", "history")
        )

    def get_serializer_class(self):
        if self.action in ("retrieve", "start_review", "review_action", "issue_certificate"):
            return ApplicationDetailSerializer
        return ApplicationListSerializer

    def perform_create(self, serializer):
        if serializer.validated_data.get('source') == 'WALK_IN':
            serializer.save(staff_captured_by=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=["post"], url_path="start_review")
    def start_review(self, request, pk=None):
        application = self.get_object()
        try:
            application.start_review(request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ApplicationDetailSerializer(application, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="review_action")
    def review_action(self, request, pk=None):
        application = self.get_object()
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        act = serializer.validated_data["action"]
        notes = serializer.validated_data["notes"]
        rejection_reason = serializer.validated_data["rejection_reason"]

        try:
            if act == ReviewActionSerializer.ACTION_APPROVE:
                centre_id = request.data.get('assigned_centre')
                if centre_id:
                    from centres.models import Centre
                    try:
                        application.assigned_centre = Centre.objects.get(pk=centre_id)
                    except Centre.DoesNotExist:
                        return Response(
                            {'detail': 'Invalid centre ID.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                if not application.assigned_centre:
                    return Response(
                        {'detail': 'assigned_centre is required to approve an application.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                application.save(update_fields=['assigned_centre'])
                application.approve(notes=notes)
                notify_application_reviewed.delay(str(application.id))
                notify_payment_required.delay(str(application.id))
            elif act == ReviewActionSerializer.ACTION_REJECT:
                application.reject(reason=rejection_reason)
                notify_application_reviewed.delay(str(application.id))
            elif act == ReviewActionSerializer.ACTION_MORE_INFO:
                application.request_more_info(notes=notes)
                notify_application_reviewed.delay(str(application.id))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ApplicationDetailSerializer(application, context={"request": request}).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def issue_certificate(self, request, pk=None):
        application = self.get_object()
        try:
            enrollment = application.enrollment
        except Enrollment.DoesNotExist:
            return Response(
                {"detail": "This application has no enrollment yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.certificates.models import Certificate
        try:
            Certificate.issue_from_enrollment(enrollment, issued_by=request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        application.refresh_from_db()
        return Response(
            ApplicationDetailSerializer(application, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        today = timezone.now().date()
        first_of_month = today.replace(day=1)

        status_counts = {
            row["status"]: row["count"]
            for row in Application.objects.values("status").annotate(count=Count("id"))
        }

        # Applications per course (top 8)
        by_course = [
            {"course": row["course__fullname"] or "Unknown", "count": row["count"]}
            for row in Application.objects.values("course__fullname")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        ]

        # Submissions per day for the last 7 days
        week_ago = today - timedelta(days=6)
        daily_qs = {
            row["day"].strftime("%a"): row["count"]
            for row in Application.objects.filter(submitted_at__date__gte=week_ago)
            .annotate(day=TruncDate("submitted_at"))
            .values("day")
            .annotate(count=Count("id"))
        }
        weekly_trend = [
            {
                "day": (week_ago + timedelta(days=i)).strftime("%a"),
                "submissions": daily_qs.get((week_ago + timedelta(days=i)).strftime("%a"), 0),
            }
            for i in range(7)
        ]

        return Response({
            "pending_review": status_counts.get(ApplicationStatus.SUBMITTED, 0),
            "under_review": status_counts.get(ApplicationStatus.UNDER_REVIEW, 0),
            "approved_awaiting_payment": status_counts.get(ApplicationStatus.PAYMENT_PENDING, 0),
            "enrolled_today": Application.objects.filter(enrolled_at__date=today).count(),
            "total_this_month": Application.objects.filter(
                created_at__date__gte=first_of_month
            ).count(),
            "by_status": status_counts,
            "by_course": by_course,
            "weekly_trend": weekly_trend,
        })


class LecturerApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A lecturer's view of their own students (FRS §3.3): applications for
    courses that have at least one CourseSchedule assigned to this lecturer,
    restricted to ENROLLED/CERTIFIED. Applications don't carry a direct FK
    to a specific intake, so this scopes at the course level like the
    schedule assignment itself does.
    """
    permission_classes = [IsLecturer]
    serializer_class = LecturerApplicationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Application.objects.none()
        return (
            Application.objects.filter(
                course__schedules__lecturer=self.request.user,
                status__in=[ApplicationStatus.ENROLLED, ApplicationStatus.CERTIFIED],
            )
            .select_related("applicant", "course", "assigned_centre")
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ApplicationDetailSerializer
        return LecturerApplicationSerializer

    @action(detail=True, methods=["post"], url_path="sign-off")
    def sign_off(self, request, pk=None):
        application = self.get_object()
        notes = request.data.get("notes", "")

        try:
            enrollment = application.enrollment
        except Enrollment.DoesNotExist:
            return Response(
                {"detail": "This application has no enrollment yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.certificates.models import Certificate
        try:
            with transaction.atomic():
                application.lecturer_sign_off(lecturer=request.user, notes=notes)
                Certificate.issue_from_enrollment(enrollment, issued_by=request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        application.refresh_from_db()
        return Response({
            "status": application.status,
            "lecturer_signed_off": True,
            "certificate_number": (
                enrollment.certificate.certificate_number
                if hasattr(enrollment, "certificate") else None
            ),
            "message": "Sign-off complete. Certificate issued and emailed to student.",
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sign_code_of_conduct(request, pk):
    try:
        app = Application.objects.get(pk=pk, applicant=request.user)
    except Application.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
    if app.status not in [
        ApplicationStatus.APPROVED,
        ApplicationStatus.PAYMENT_PENDING,
        ApplicationStatus.PAYMENT_CONFIRMED,
    ]:
        return Response(
            {'detail': 'Code of conduct can only be signed after approval.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    app.code_of_conduct_signed = True
    app.code_of_conduct_signed_at = timezone.now()
    app.save(update_fields=['code_of_conduct_signed', 'code_of_conduct_signed_at'])
    return Response({'signed': True, 'signed_at': app.code_of_conduct_signed_at})


@api_view(['POST'])
@permission_classes([IsAdminOrReviewer])
def de_enrol_student(request, pk):
    from apps.enrollments.tasks import unenrol_from_moodle
    try:
        app = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
    de_type = request.data.get('type', 'MANDATORY')
    reason = request.data.get('reason', '')
    if not reason:
        return Response({'detail': 'reason is required.'}, status=http_status.HTTP_400_BAD_REQUEST)
    if de_type not in ('MANDATORY', 'VOLUNTARY'):
        return Response(
            {'detail': 'type must be MANDATORY or VOLUNTARY.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    try:
        enrollment = app.enrollment
    except Enrollment.DoesNotExist:
        return Response(
            {'detail': 'No enrollment found for this application.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    unenrol_from_moodle.delay(str(enrollment.pk), de_type, reason)
    return Response({'status': 'de_enrolment_queued'})


@api_view(['POST'])
@permission_classes([IsAdminOrReviewer])
def create_walkin_application(request):
    from django.contrib.auth import get_user_model
    from apps.courses.models import Course
    from centres.models import Centre

    User = get_user_model()
    email = request.data.get('student_email', '').lower().strip()
    if not email:
        return Response({'detail': 'student_email is required.'}, status=http_status.HTTP_400_BAD_REQUEST)

    course_id = request.data.get('course')
    if not course_id:
        return Response({'detail': 'course is required.'}, status=http_status.HTTP_400_BAD_REQUEST)
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return Response({'detail': 'Course not found.'}, status=http_status.HTTP_400_BAD_REQUEST)

    student, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': request.data.get('student_first_name', ''),
            'last_name': request.data.get('student_last_name', ''),
            'phone': request.data.get('student_phone', ''),
            'role': 'STUDENT',
            'is_active': True,
        }
    )
    if created:
        student.set_unusable_password()
        student.save()

    preferred_centre = None
    centre_id = request.data.get('preferred_centre')
    if centre_id:
        try:
            preferred_centre = Centre.objects.get(pk=centre_id)
        except Centre.DoesNotExist:
            pass

    app = Application.objects.create(
        applicant=student,
        course=course,
        hexco_level=request.data.get('hexco_level', ''),
        department=request.data.get('department', ''),
        student_category=request.data.get('student_category', ''),
        preferred_centre=preferred_centre,
        motivation=request.data.get('motivation', 'Walk-in registration'),
        source='WALK_IN',
        staff_captured_by=request.user,
        status=ApplicationStatus.SUBMITTED,
    )
    app._record_transition(ApplicationStatus.SUBMITTED, request.user, 'Walk-in registration')

    return Response({'id': str(app.id), 'ref': app.ref, 'status': app.status}, status=http_status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def track_application(request, ref):
    try:
        app = Application.objects.select_related(
            'assigned_centre', 'course'
        ).get(ref=ref)
    except Application.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)

    history = app.history.order_by('changed_at').values(
        'from_status', 'to_status', 'changed_at', 'notes'
    )
    return Response({
        'ref': app.ref,
        'status': app.status,
        'status_display': app.get_status_display(),
        'course_name': app.course.fullname if app.course else None,
        'assigned_centre': app.assigned_centre.name if app.assigned_centre else None,
        'last_updated': app.updated_at,
        'history': list(history),
    })
