from rest_framework import permissions


class IsNoteOwnerOrCEO(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff or hasattr(request.user, 'managed_branches'):
            return True

        return obj.author == request.user