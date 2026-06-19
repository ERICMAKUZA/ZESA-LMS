from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin

from .models import Course
from .serializers import CourseSerializer, CourseSummarySerializer
from .tasks import sync_courses_from_moodle


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
    queryset = Course.objects.all().select_related("category")
    serializer_class = CourseSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["is_active", "category", "requires_approval"]
    search_fields = ["fullname", "shortname"]
    ordering_fields = ["fullname", "price", "enrolled_count"]


class MoodleSyncView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        task = sync_courses_from_moodle.delay()
        return Response({"task_id": task.id, "status": "queued"}, status=status.HTTP_202_ACCEPTED)
