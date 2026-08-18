from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    LogoutView,
    MeView,
    MoodleSsoConsumeView,
    MoodleSsoStartView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("moodle-sso/", MoodleSsoStartView.as_view(), name="auth-moodle-sso"),
    path("moodle-sso/consume/", MoodleSsoConsumeView.as_view(), name="auth-moodle-sso-consume"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
]
