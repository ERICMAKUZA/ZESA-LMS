from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminApplicationViewSet, StudentApplicationViewSet

student_router = DefaultRouter()
student_router.register("my-applications", StudentApplicationViewSet, basename="my-application")

admin_router = DefaultRouter()
admin_router.register("admin/applications", AdminApplicationViewSet, basename="admin-application")

urlpatterns = [
    path("", include(student_router.urls)),
    path("", include(admin_router.urls)),
]
