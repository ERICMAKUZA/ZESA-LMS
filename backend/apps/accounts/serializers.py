from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "full_name",
            "employee_id", "student_id", "zntc_email", "ec_number",
            "department", "phone", "role", "is_active", "date_joined",
        )
        read_only_fields = ("id", "email", "date_joined", "student_id", "zntc_email")


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "email", "first_name", "last_name", "employee_id",
            "department", "phone", "password", "password_confirm",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "department", "phone")


class TokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        token["role"] = user.role
        token["employee_id"] = user.employee_id or ""
        token["ec_number"] = user.ec_number or ""
        return token

    def validate(self, attrs):
        # SimpleJWT is stateless and never calls django.contrib.auth.login(),
        # so django.contrib.auth.signals.user_logged_in never fires here —
        # this is the actual point a login succeeds, hooked explicitly.
        data = super().validate(attrs)
        from apps.core.models import AuditLog
        AuditLog.log(
            actor=self.user, action=AuditLog.Action.LOGIN, instance=self.user,
            request=self.context.get("request"),
            notes=f"User logged in: {self.user.email} (role={self.user.role})",
        )
        return data
