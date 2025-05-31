from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import RecipeSerializer

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Recipe, Ingredient
from .forms import RecipeForm

# View to see all recipes from the database
def recipes_list(request):
    recipes = Recipe.objects_all()  # Retrieve all Recipe objects from the database
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes}) #shows recipe.html

# View to see specific details of a meal
def recipe_detail(request, pk):
    recipes = get_object_or_404(Recipe, pk=pk) # Get the recipe by primary key (pk) or return a 404 if not found
    return render(request, 'recipes/recipe_detail.html', {'recipes': recipes})

# View to create a new recipe
def recipe_create(request):
    if request.method == "POST":
        # If the request is a POST, bind the form with the submitted data
        form = RecipeForm(request.POST)
        if form.is_valid():  # Check if the form data is valid
            recipe = form.save(commit=False)  # Create the recipe object but don't save yet
            recipe.user = request.user  # Associate the logged-in user with the recipe
            recipe.save()  # Save the recipe to the database
            return redirect('recipe_detail', pk=recipe.pk)  # Redirect to the recipe detail page
    else:
        # If the request is not a POST, create an empty form instance
        form = RecipeForm()
    # Render the 'recipe_form.html' template with the form
    return render(request, 'recipes/recipe_form.html', {'form': form})

def recipe_update(request, pk):
    # Get the recipe by primary key (pk) or return a 404 if not found
     recipe = get_object_or_404(Recipe, pk=pk)
     if request.method == "POST":
        # If the request is a POST, bind the form with the submitted data and the existing recipe
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():  # Check if the form data is valid
            form.save()  # Save the updated recipe to the database
            return redirect('recipe_detail', pk=recipe.pk)  # Redirect to the recipe detail page
        else:
        # If the request is not a POST, create a form instance with the current recipe data
            form = RecipeForm(instance=recipe)
    # Render the 'recipe_form.html' template with the form
     return render(request, 'recipes/recipe_form.html', {'form': form})

# View to delete a recipe
def recipe_delete(request, pk):
    # Get the recipe by primary key (pk) or return a 404 if not found
    recipe = get_object_or_404(Recipe, pk=pk)
    recipe.delete()  # Delete the recipe from the database
    return redirect('recipe_list')  # Redirect to the recipe list page

# Filter recipes that contain any of the available ingredients
def suggest_meals(available_ingredients):
    return Recipe.objects.filter(ingredients__in=available_ingredients).distinct()

#View to handle suggestions
def recipe_suggest(request):
    if request.method == "POST":
        ingredient_names = request.POST.getlist('ingredients')  # Get list of ingredient names
        ingredients = Ingredient.objects.filter(name__in=ingredient_names)  # Fetch ingredients from DB
        suggested_recipes = suggest_meals(ingredients)  # Get suggested recipes
        return render(request, 'recipes/recipe_suggest.html', {'recipes': suggested_recipes})
    return render(request, 'recipes/recipe_suggest.html')  # Render suggestion form
class RecipeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        form = RecipeForm(request.data)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.user = request.user
            recipe.save()
            return Response({'message': 'Recipe created successfully!'}, status=201)


class UserRecipesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recipes = Recipe.objects.filter(user=request.user)
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)