from rest_framework import permissions

class IsVerifiedContributor(permissions.BasePermission):
    """
    Custom permission to only allow verified contributors to create, update, or delete recipes.
    """
    message = "You must be a verified contributor to perform this action."

    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for anyone (to view recipes)
        if request.method in permissions.SAFE_METHODS:
            return True

        # For POST, PUT, PATCH, DELETE, check if user is authenticated and a verified contributor
        return request.user and request.user.is_authenticated and request.user.is_verified_contributor

    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, OPTIONS requests for anyone (to view a specific recipe)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Object-level permissions: only the contributor who created the recipe can update/delete it
        # Or, if an admin needs to be able to modify, add that logic here.
        return request.user and request.user.is_authenticated and obj.contributor == request.user