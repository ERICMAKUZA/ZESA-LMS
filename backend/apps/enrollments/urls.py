from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminEnrollmentViewSet, EnrollmentStatusView, StudentEnrollmentListView

admin_router = DefaultRouter()
admin_router.register("admin/enrollments", AdminEnrollmentViewSet, basename="admin-enrollment")

urlpatterns = [
    path("enrollments/", StudentEnrollmentListView.as_view(), name="student-enrollment-list"),
    path("enrollments/<uuid:application_id>/", EnrollmentStatusView.as_view(), name="enrollment-status"),
    path("", include(admin_router.urls)),
]
