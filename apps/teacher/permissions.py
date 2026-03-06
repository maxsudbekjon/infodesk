from rest_framework.permissions import BasePermission

from apps.settings.models import Organization


class TeacherImagePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
                obj.user == request.user or
                obj.branch.organization.owner == request.user
        )


class IsOrganizationOwner(BasePermission):
    def has_permission(self, request, view):
        return Organization.objects.filter(owner=request.user).exists()

    def has_object_permission(self, request, view, obj):
        return obj.branch.organization.owner == request.user
