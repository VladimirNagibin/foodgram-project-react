from rest_framework import permissions


class IsAuthenticatedOrAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        return bool(
            request.method in permissions.SAFE_METHODS or (
                request.user and obj.author == request.user
            )
        )


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            (request.user.is_authenticated and request.user.is_admin)
            or request.method in permissions.SAFE_METHODS
        )


class IsAdminOrAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, review_or_comment_obj):
        return bool(
            request.method in permissions.SAFE_METHODS or (
                request.user and review_or_comment_obj.author == request.user
            ) or request.user.is_admin or request.user.is_moderator
        )


class IsAdminOrSuperUserOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin