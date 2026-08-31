from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.accounts.views import AdminLecturerListView, AdminUserListView, DemoAccountsView, MeView

urlpatterns = [
    path("django-admin/", admin.site.urls),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    path("api/auth/", include("apps.accounts.urls")),
    path("api/users/me/", MeView.as_view(), name="user-me"),
    path("api/admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("api/admin/lecturers/", AdminLecturerListView.as_view(), name="admin-lecturer-list"),
    path("api/demo-accounts/", DemoAccountsView.as_view(), name="demo-accounts"),

    path("api/centres/", include("centres.urls")),
    path("api/courses/", include("apps.courses.urls")),
    path("api/", include("apps.applications.urls")),
    path("api/", include("apps.workflows.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/", include("apps.enrollments.urls")),
    path("api/certs/", include("apps.certificates.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/audit/", include("apps.core.urls")),
]
