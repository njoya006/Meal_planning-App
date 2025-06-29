from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import redirect
from .models import CustomUser, DietaryPreference, VerificationApplication

# Register your CustomUser model with the admin site
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Customize how your CustomUser model appears in the admin
    # You might want to add 'role' and 'is_verified_contributor' to fieldsets or list_display
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'role', 
        'is_verified_contributor', 'verification_status', 'phone_number', 
        'date_of_birth', 'location'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'location')
    readonly_fields = ('last_login', 'date_joined', 'verified_at', 'verified_by')
    list_filter = ('role', 'is_verified_contributor', 'verification_status', 'is_active', 'is_staff')
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'location', 'profile_photo', 'basic_ingredients')}),
        ('Verification', {'fields': ('verification_status', 'verified_at', 'verified_by')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'role', 'is_verified_contributor')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'is_verified_contributor', 'region')}),
    )

@admin.register(DietaryPreference)
class DietaryPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferences')
    search_fields = ('user__username', 'user__email', 'preferences')

@admin.register(VerificationApplication)
class VerificationApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by', 
        'application_actions'
    )
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('user__username', 'user__email', 'full_name', 'specialties')
    readonly_fields = ('submitted_at', 'reviewed_at')
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Application Info', {
            'fields': ('user', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by')
        }),
        ('Applicant Details', {
            'fields': ('full_name', 'cooking_experience', 'specialties', 'motivation')
        }),
        ('Additional Info', {
            'fields': ('social_media_links', 'sample_recipes')
        }),
        ('Admin Review', {
            'fields': ('admin_notes',)
        }),
    )
    
    def application_actions(self, obj):
        """Custom actions for approving/rejecting applications."""
        if obj.status == 'pending':
            approve_url = f'/admin/users/verificationapplication/{obj.pk}/approve/'
            reject_url = f'/admin/users/verificationapplication/{obj.pk}/reject/'
            return format_html(
                '<a class="button" href="{}">Approve</a> '
                '<a class="button" href="{}">Reject</a>',
                approve_url, reject_url
            )
        return obj.status.title()
    
    application_actions.short_description = 'Actions'
    
    def approve_application(self, request, application_id):
        """Custom admin action to approve application."""
        try:
            application = VerificationApplication.objects.get(pk=application_id)
            application.approve(request.user)
            self.message_user(request, f'Application for {application.user.username} approved!')
        except VerificationApplication.DoesNotExist:
            self.message_user(request, 'Application not found!', level='ERROR')
        return redirect('admin:users_verificationapplication_changelist')
    
    def reject_application(self, request, application_id):
        """Custom admin action to reject application."""
        try:
            application = VerificationApplication.objects.get(pk=application_id)
            application.reject(request.user, "Rejected through admin interface")
            self.message_user(request, f'Application for {application.user.username} rejected!')
        except VerificationApplication.DoesNotExist:
            self.message_user(request, 'Application not found!', level='ERROR')
        return redirect('admin:users_verificationapplication_changelist')
