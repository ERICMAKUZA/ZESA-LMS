from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminApplicationViewSet, StudentApplicationViewSet, de_enrol_student, sign_code_of_conduct, track_application

student_router = DefaultRouter()
student_router.register("my-applications", StudentApplicationViewSet, basename="my-application")

admin_router = DefaultRouter()
admin_router.register("admin/applications", AdminApplicationViewSet, basename="admin-application")

urlpatterns = [
    path("", include(student_router.urls)),
    path("", include(admin_router.urls)),
    path("track/<str:ref>/", track_application, name="track-application"),
    path("my-applications/<uuid:pk>/sign-code-of-conduct/", sign_code_of_conduct, name="sign-code-of-conduct"),
    path("admin/applications/<uuid:pk>/de-enrol/", de_enrol_student, name="de-enrol"),
]
