# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
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

    def _str_(self):
        return self.username

class DietaryPreference(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='dietary_preferences')
    # This will be a comma-separated string for simplicity
    # E.g., "vegetarian,gluten-free,peanut-allergy"
    preferences = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Preferences for {self.user.username}"