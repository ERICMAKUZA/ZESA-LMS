from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReportViewSet, ShortlistReportView

router = DefaultRouter()
router.register("", ReportViewSet, basename="report")

urlpatterns = [
    path("shortlist/", ShortlistReportView.as_view(), name="shortlist-report"),
    path("", include(router.urls)),
]
