from django.contrib import admin
# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your CustomUser model with the admin site
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Customize how your CustomUser model appears in the admin
    # You might want to add 'role' and 'is_verified_contributor' to fieldsets or list_display
    list_display = UserAdmin.list_display + ('role', 'is_verified_contributor', 'region')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'is_verified_contributor', 'region')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'is_verified_contributor', 'region')}),
    )

# Register your models here.
