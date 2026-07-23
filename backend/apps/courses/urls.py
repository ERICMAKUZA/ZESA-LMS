from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminCourseViewSet, CourseCategoryListView, CourseDetailView, CourseListView,
    MoodleSyncView, lecturer_schedule_list, schedule_list, submit_enquiry,
)

router = DefaultRouter()
router.register("admin", AdminCourseViewSet, basename="admin-course")

urlpatterns = [
    # Explicit paths must come before "<int:pk>/" to avoid pk-collision
    path("lecturer/schedules/", lecturer_schedule_list, name="lecturer-schedule-list"),
    path("categories/", CourseCategoryListView.as_view(), name="course-category-list"),
    path("sync/", MoodleSyncView.as_view(), name="course-moodle-sync"),
    path("schedule/", schedule_list, name="schedule-list"),
    path("enquiries/", submit_enquiry, name="submit-enquiry"),
    path("", include(router.urls)),
    path("", CourseListView.as_view(), name="course-list"),
    path("<int:pk>/", CourseDetailView.as_view(), name="course-detail"),
]
