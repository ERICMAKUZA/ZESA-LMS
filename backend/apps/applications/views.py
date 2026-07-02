from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrReviewer

from .filters import ApplicationFilter
from .models import Application, ApplicationStatus
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationDetailSerializer,
    ApplicationListSerializer,
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
        if self.action == "create":
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
            .select_related("applicant", "course", "reviewer")
            .prefetch_related("documents", "history")
        )

    def get_serializer_class(self):
        if self.action in ("retrieve", "start_review", "review_action"):
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
