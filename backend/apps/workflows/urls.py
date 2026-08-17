from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApprovalStepViewSet, NotificationViewSet

router = DefaultRouter()
router.register("workflow-steps", ApprovalStepViewSet, basename="workflow-step")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
]
