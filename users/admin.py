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
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_verified_contributor', 'phone_number', 'date_of_birth', 'location')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'location')
    readonly_fields = ('last_login', 'date_joined')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'location', 'profile_photo', 'basic_ingredients')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'role', 'is_verified_contributor')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'is_verified_contributor', 'region')}),
    )

# Register your models here.
