from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AcademicCalendarEventView,
    AdminCourseViewSet, CertificationTypeViewSet, CourseCategoryListView,
    CourseDetailView, CourseListView, CourseTypeViewSet, DepartmentViewSet,
    GradeBandViewSet, QualificationProfileViewSet, QualificationRequirementViewSet,
    MoodleSyncView, lecturer_schedule_list, schedule_list, submit_enquiry,
    training_selection,
)

router = DefaultRouter()
router.register("admin", AdminCourseViewSet, basename="admin-course")

training_router = DefaultRouter()
training_router.register("departments", DepartmentViewSet, basename="training-department")
training_router.register("course-types", CourseTypeViewSet, basename="training-course-type")
training_router.register("certification-types", CertificationTypeViewSet, basename="training-cert-type")
training_router.register("grade-bands", GradeBandViewSet, basename="training-grade-band")
training_router.register("qualification-profiles", QualificationProfileViewSet, basename="training-profile")
training_router.register("qualification-requirements", QualificationRequirementViewSet, basename="training-requirement")

urlpatterns = [
    # Explicit paths must come before "<int:pk>/" to avoid pk-collision
    path("lecturer/schedules/", lecturer_schedule_list, name="lecturer-schedule-list"),
    path("categories/", CourseCategoryListView.as_view(), name="course-category-list"),
    path("calendar-events/", AcademicCalendarEventView.as_view(), name="calendar-event-list-create"),
    path("training/selection/", training_selection, name="course-training-selection"),
    path("sync/", MoodleSyncView.as_view(), name="course-moodle-sync"),
    path("schedule/", schedule_list, name="schedule-list"),
    path("enquiries/", submit_enquiry, name="submit-enquiry"),
    path("training/", include(training_router.urls)),
    path("", CourseListView.as_view(), name="course-list"),
    path("", include(router.urls)),
    path("<int:pk>/", CourseDetailView.as_view(), name="course-detail"),
]
