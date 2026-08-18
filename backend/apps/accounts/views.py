import hmac

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.permissions import IsAdmin

from .models import User
from .moodle_sso import (
    MoodleSsoNotConfigured,
    build_moodle_sso_url,
    consume_moodle_sso_code,
    issue_moodle_sso_code,
)
from .serializers import TokenObtainPairSerializer, UserCreateSerializer, UserSerializer, UserUpdateSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        from apps.workflows.services import queue_notification

        queue_notification(
            recipient=user,
            subject="Welcome to ZESA National Training Centre",
            message=(
                f"Hi {user.first_name},\n\n"
                "Your ZESA National Training Centre student account has been created.\n\n"
                "You can now browse courses, submit applications, and track your enrolment from the portal."
            ),
            action_url="/courses",
        )


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Purely an audit hook — tokens are stateless (no blacklist configured),
    so "logging out" is really the client discarding its tokens. This just
    records that it happened before the frontend clears localStorage.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from apps.core.models import AuditLog
        AuditLog.log(
            actor=request.user, action=AuditLog.Action.LOGOUT, instance=request.user,
            request=request, notes=f"User logged out: {request.user.email}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MoodleSsoStartView(APIView):
    """Issue an opaque code for the logged-in portal user to enter Moodle."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            code = issue_moodle_sso_code(request.user)
        except MoodleSsoNotConfigured:
            return Response(
                {"detail": "Moodle single sign-on is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except RuntimeError:
            return Response(
                {"detail": "Unable to start Moodle single sign-on. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"url": build_moodle_sso_url(code)})


class MoodleSsoConsumeView(APIView):
    """Allow Moodle to redeem an SSO code over the internal cluster network."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        shared_secret = settings.MOODLE_SSO_SHARED_SECRET
        presented_secret = request.headers.get("X-ZESA-SSO-Secret", "")
        if not shared_secret or not hmac.compare_digest(presented_secret, shared_secret):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        payload = consume_moodle_sso_code(request.data.get("code", ""))
        if payload is None:
            return Response({"detail": "This Moodle sign-on link is invalid or has expired."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(payload)


class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by("last_name", "first_name")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name", "employee_id", "department"]
    ordering_fields = ["last_name", "date_joined", "role"]


class DemoAccountsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not settings.DEMO_MODE:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        primary = [
            {
                "label": "Student (fresh applicant)",
                "email": "student.demo@zesa.co.zw",
                "role": "STUDENT",
            },
            {
                "label": "Reviewer / Approver",
                "email": "approver.demo@zesa.co.zw",
                "role": "REVIEWER",
            },
        ]

        all_accounts = [
            {"label": "Student — submitted",        "email": "student.demo@zesa.co.zw",        "role": "STUDENT"},
            {"label": "Student — under review",     "email": "farai.chikomba@zesa.co.zw",      "role": "STUDENT"},
            {"label": "Student — needs more info",  "email": "nyasha.mupambi@zesa.co.zw",      "role": "STUDENT"},
            {"label": "Student — approved",         "email": "blessing.zulu@zesa.co.zw",       "role": "STUDENT"},
            {"label": "Student — payment pending",  "email": "simbarashe.dube@zesa.co.zw",     "role": "STUDENT"},
            {"label": "Student — payment confirmed","email": "tendai.moyo@zesa.co.zw",         "role": "STUDENT"},
            {"label": "Student — enrolled",         "email": "rumbidzai.chikomo@zesa.co.zw",   "role": "STUDENT"},
            {"label": "Student — rejected",         "email": "tinashe.mhuru@zesa.co.zw",       "role": "STUDENT"},
            {"label": "Reviewer / Approver",        "email": "approver.demo@zesa.co.zw",       "role": "REVIEWER"},
            {"label": "Admin",                      "email": "admin@zesa.co.zw",               "role": "ADMIN"},
        ]

        return Response({"primary": primary, "all": all_accounts})
