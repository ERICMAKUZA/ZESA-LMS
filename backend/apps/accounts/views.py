from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.permissions import IsAdmin

from .models import User
from .serializers import TokenObtainPairSerializer, UserCreateSerializer, UserSerializer, UserUpdateSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


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
