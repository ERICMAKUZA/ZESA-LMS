from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminCourseViewSet, CourseDetailView, CourseListView, MoodleSyncView

router = DefaultRouter()
router.register("admin", AdminCourseViewSet, basename="admin-course")

urlpatterns = [
    path("", CourseListView.as_view(), name="course-list"),
    path("<int:pk>/", CourseDetailView.as_view(), name="course-detail"),
    path("sync/", MoodleSyncView.as_view(), name="course-moodle-sync"),
    path("", include(router.urls)),
]
