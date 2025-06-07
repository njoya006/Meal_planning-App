# planner/permissions.py

from rest_framework import permissions

class IsVerifiedContributor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'is_verified_contributor', False)
