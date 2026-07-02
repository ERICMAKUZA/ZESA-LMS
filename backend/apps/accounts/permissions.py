from rest_framework.permissions import BasePermission

from .models import User


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.ADMIN, User.Role.SUPERADMIN)
        )


class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.REVIEWER
        )


class IsFinance(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.FINANCE
        )


class IsAdminOrReviewer(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.ADMIN, User.Role.SUPERADMIN, User.Role.REVIEWER)
        )


class IsLecturer(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.LECTURER
        )


class IsCentreAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.CENTRE_ADMIN, User.Role.ADMIN, User.Role.SUPERADMIN)
        )


class IsAdminOrReviewerOrCentreAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                User.Role.ADMIN, User.Role.SUPERADMIN,
                User.Role.REVIEWER, User.Role.CENTRE_ADMIN,
            )
        )
