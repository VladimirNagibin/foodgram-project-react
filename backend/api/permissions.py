from rest_framework import permissions


class IsAuthenticatedOrAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS or (
                request.user and obj.author == request.user
            )
        )
