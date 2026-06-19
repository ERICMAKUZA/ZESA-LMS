from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApprovalStepViewSet

router = DefaultRouter()
router.register("workflow-steps", ApprovalStepViewSet, basename="workflow-step")

urlpatterns = [
    path("", include(router.urls)),
]
