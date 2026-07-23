from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminApplicationViewSet, LecturerApplicationViewSet, StudentApplicationViewSet,
    create_walkin_application, de_enrol_student,
    sign_code_of_conduct, track_application,
)

student_router = DefaultRouter()
student_router.register("my-applications", StudentApplicationViewSet, basename="my-application")

admin_router = DefaultRouter()
admin_router.register("admin/applications", AdminApplicationViewSet, basename="admin-application")

lecturer_router = DefaultRouter()
lecturer_router.register("lecturer/applications", LecturerApplicationViewSet, basename="lecturer-application")

urlpatterns = [
    # Explicit paths must come before router includes to avoid pk-collision
    path("admin/applications/walk-in/", create_walkin_application, name="walk-in-application"),
    path("admin/applications/<uuid:pk>/de-enrol/", de_enrol_student, name="de-enrol"),
    path("my-applications/<uuid:pk>/sign-code-of-conduct/", sign_code_of_conduct, name="sign-code-of-conduct"),
    path("track/<str:ref>/", track_application, name="track-application"),
    path("", include(student_router.urls)),
    path("", include(admin_router.urls)),
    path("", include(lecturer_router.urls)),
]
