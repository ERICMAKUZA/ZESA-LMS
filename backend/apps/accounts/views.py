from rest_framework import generics, permissions
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
