"""User models for the ChopSmo application."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """Extended user model with additional fields for the recipe application."""
    
    USER = 'user'
    CONTRIBUTOR = 'contributor'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (USER, 'User'),
        (CONTRIBUTOR, 'Contributor'),
        (ADMIN, 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=USER)
    is_verified_contributor = models.BooleanField(default=False)
    region = models.CharField(
        max_length=10, 
        default='global', 
        help_text="User's region for ingredient localization."
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        help_text="User's phone number"
    )
    date_of_birth = models.DateField(
        blank=True, 
        null=True, 
        help_text="User's date of birth"
    )
    location = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="User's location (city, region, etc.)"
    )
    basic_ingredients = models.TextField(
        blank=True, 
        null=True, 
        help_text="User's basic ingredients as free text (comma-separated or similar)"
    )
    profile_photo = models.ImageField(
        upload_to='profile_photos/', 
        null=True, 
        blank=True, 
        help_text="User's profile photo."
    )

    # Add verification fields
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Verification'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('none', 'Not Applied'),
        ],
        default='none',
        help_text="User's verification status"
    )
    verified_at = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="When the user was verified"
    )
    verified_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_users',
        help_text="Admin who verified this user"
    )

    def __str__(self):
        return self.username


class DietaryPreference(models.Model):
    """Model to store user dietary preferences."""
    
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='dietary_preferences'
    )
    preferences = models.TextField(
        blank=True, 
        default="", 
        help_text="Comma-separated dietary preferences, e.g. 'vegetarian,gluten-free,peanut-allergy'"
    )

    def __str__(self):
        return f"{self.user.username}'s dietary preferences"
    def __str__(self):
        return f"Preferences for {self.user.username}"


class VerificationApplication(models.Model):
    """Model to store user verification applications."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='verification_application'
    )
    
    # Application details
    full_name = models.CharField(max_length=255, help_text="Full legal name")
    cooking_experience = models.TextField(help_text="Describe your cooking experience")
    specialties = models.TextField(help_text="Your cooking specialties or cuisines")
    social_media_links = models.TextField(
        blank=True, 
        help_text="Links to your social media profiles (optional)"
    )
    sample_recipes = models.TextField(
        blank=True,
        help_text="Links or descriptions of your sample recipes (optional)"
    )
    motivation = models.TextField(help_text="Why do you want to become a verified contributor?")
    
    # Application status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes from admin review"
    )
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"
    
    def approve(self, admin_user):
        """Approve the verification application."""
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.save()
        
        # Update user verification status
        self.user.is_verified_contributor = True
        self.user.verification_status = 'approved'
        self.user.verified_at = timezone.now()
        self.user.verified_by = admin_user
        self.user.save()
    
    def reject(self, admin_user, reason=""):
        """Reject the verification application."""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        if reason:
            self.admin_notes = reason
        self.save()
        
        # Update user verification status
        self.user.verification_status = 'rejected'
        self.user.save()