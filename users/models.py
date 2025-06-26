"""User models for the ChopSmo application."""

from django.contrib.auth.models import AbstractUser
from django.db import models


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