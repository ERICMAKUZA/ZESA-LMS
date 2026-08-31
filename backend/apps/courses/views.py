import datetime
import logging

from django.db import transaction
from django.db.models import Count, Q
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin, IsLecturer

from .models import Course, CourseCategory, CourseSchedule, Enquiry
from .serializers import (
    CourseCategoryWithCountSerializer,
    CourseScheduleSerializer,
    CourseSerializer,
    CourseSummarySerializer,
)
from .services import MoodleClient
from .tasks import sync_courses_from_moodle

logger = logging.getLogger(__name__)


class CourseCategoryListView(generics.ListAPIView):
    serializer_class = CourseCategoryWithCountSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return CourseCategory.objects.annotate(
            course_count=Count('courses', filter=Q(courses__is_active=True))
        ).order_by('name')


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.filter(is_active=True).select_related("category")
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["category", "requires_approval"]
    search_fields = ["fullname", "shortname", "summary"]
    ordering_fields = ["fullname", "price", "enrolled_count", "created_at"]


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.filter(is_active=True).select_related("category")
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]


class AdminCourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().select_related("category").prefetch_related("lecturers")
    serializer_class = CourseSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer):
        category = serializer.validated_data["category"]
        initial_schedule = serializer.validated_data["initial_schedule"]
        moodle_client = MoodleClient()
        moodle_course = None
        try:
            moodle_course = moodle_client.create_course(
                shortname=serializer.validated_data["shortname"],
                fullname=serializer.validated_data["fullname"],
                category_id=category.moodle_id,
                summary=serializer.validated_data.get("summary", ""),
                visible=serializer.validated_data.get("is_active", True),
            )
            with transaction.atomic():
                course = serializer.save(moodle_course_id=moodle_course["id"])
                CourseSchedule.objects.create(course=course, **initial_schedule)
        except Exception as exc:
            if moodle_course:
                try:
                    moodle_client.delete_course(moodle_course["id"])
                except Exception:
                    logger.exception(
                        "Could not clean up Moodle course %s after portal course creation failed.",
                        moodle_course["id"],
                    )
            raise ValidationError(
                {"moodle": f"The course could not be created in Moodle: {exc}"}
            ) from exc

        if not course.is_active:
            return

        from apps.accounts.models import User
        from apps.workflows.services import queue_notifications

        try:
            queue_notifications(
                recipients=User.objects.filter(role=User.Role.STUDENT, is_active=True),
                subject=f"New course available: {course.fullname}",
                message=(
                    f"A new ZNTC course is now available: {course.fullname}.\n\n"
                    f"Course code: {course.shortname}\n"
                    "Log in to the ZESA training portal to view details and apply."
                ),
                action_url=f"/courses/{course.id}",
            )
        except Exception:
            logger.exception("Could not queue new-course notifications for course %s.", course.id)

    def perform_update(self, serializer):
        course = serializer.instance
        category = serializer.validated_data.get("category", course.category)
        if not category:
            raise ValidationError({"category_id": "A course category is required."})

        try:
            MoodleClient().update_course(
                course_id=course.moodle_course_id,
                shortname=serializer.validated_data.get("shortname", course.shortname),
                fullname=serializer.validated_data.get("fullname", course.fullname),
                category_id=category.moodle_id,
                summary=serializer.validated_data.get("summary", course.summary),
                visible=serializer.validated_data.get("is_active", course.is_active),
            )
        except Exception as exc:
            raise ValidationError(
                {"moodle": f"The course could not be updated in Moodle: {exc}"}
            ) from exc

        serializer.save()

    filterset_fields = ["is_active", "category", "requires_approval"]
    search_fields = ["fullname", "shortname"]
    ordering_fields = ["fullname", "price", "enrolled_count"]


class MoodleSyncView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        task = sync_courses_from_moodle.delay()
        return Response({"task_id": task.id, "status": "queued"}, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([AllowAny])
def schedule_list(request):
    """
    Public endpoint: GET /api/schedule/
    Optional params: ?year=2026 ?month=3 ?category=<category_id>
    Returns all upcoming schedules grouped by month.
    """
    today = datetime.date.today()
    year = int(request.query_params.get('year', today.year))
    month = request.query_params.get('month')
    category = request.query_params.get('category')

    qs = CourseSchedule.objects.select_related(
        'course', 'course__category'
    ).filter(year=year, status__in=['OPEN', 'FULL'])

    if month:
        qs = qs.filter(month=int(month))
    if category:
        qs = qs.filter(course__category_id=category)

    grouped = {}
    for s in qs.order_by('month', 'week_in_month'):
        key = s.month
        if key not in grouped:
            grouped[key] = {
                'month': key,
                'month_display': s.get_month_display(),
                'schedules': [],
            }
        grouped[key]['schedules'].append(CourseScheduleSerializer(s).data)

    return Response(list(grouped.values()))


@api_view(['GET'])
@permission_classes([IsLecturer])
def lecturer_schedule_list(request):
    """
    GET /api/courses/lecturer/schedules/ — intakes for courses assigned to
    the logged-in lecturer.
    """
    qs = CourseSchedule.objects.filter(
        Q(course__lecturers=request.user) | Q(lecturer=request.user)
    ).select_related('course', 'course__category').distinct().order_by('-year', '-month')
    return Response(CourseScheduleSerializer(qs, many=True).data)


from rest_framework import serializers as drf_serializers  # noqa: E402


class EnquiryCreateSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ['full_name', 'email', 'phone', 'organisation',
                  'enquiry_type', 'course', 'message']


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_enquiry(request):
    from django.conf import settings
    from django.core.mail import send_mail

    serializer = EnquiryCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    enquiry = serializer.save()

    ref = f"ENQ-{str(enquiry.id)[:8].upper()}"

    send_mail(
        subject="Thank you for your enquiry — ZNTC Training Centre",
        message=(
            f"Dear {enquiry.full_name},\n\n"
            "Thank you for contacting the ZESA National Training Centre.\n"
            "We have received your enquiry and will respond within 2 business days.\n\n"
            f"Your enquiry reference: {ref}\n"
            f"Topic: {enquiry.get_enquiry_type_display()}\n\n"
            "For urgent matters please call us on +263 242 000 000.\n\n"
            "Regards,\nZESA National Training Centre\n"
            "Ganges Road, Workington, Harare"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[enquiry.email],
        fail_silently=True,
    )

    send_mail(
        subject=f"New Enquiry: {enquiry.get_enquiry_type_display()} — {enquiry.full_name}",
        message=(
            f"Name: {enquiry.full_name}\n"
            f"Email: {enquiry.email}\n"
            f"Phone: {enquiry.phone or 'Not provided'}\n"
            f"Organisation: {enquiry.organisation or 'Not provided'}\n"
            f"Type: {enquiry.get_enquiry_type_display()}\n"
            f"Course: {enquiry.course.fullname if enquiry.course else 'Not specified'}\n\n"
            f"Message:\n{enquiry.message}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[getattr(settings, 'TRAINING_ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)],
        fail_silently=True,
    )

    return Response({
        'ref': ref,
        'message': 'Enquiry submitted successfully. We will respond within 2 business days.',
    }, status=201)
