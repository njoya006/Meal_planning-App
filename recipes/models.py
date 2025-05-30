
from django.db import models
from django.contrib.auth.models import User

# An ingredient model
class Ingredient(models.Model):
    name = models.CharField(max_length=100)  # Name of the ingredient

    def __str__(self):
        return self.name  # Return the name of the ingredient

# A recipe Model.
class Recipe(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions= models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ingredients = models.ManyToManyField(Ingredient) 

    def __str__(self):
        return self.title
    

