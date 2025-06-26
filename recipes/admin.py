from django.contrib import admin
from .models import Recipe, Ingredient, RecipeIngredient, BadIngredient, IngredientSubstitution, IngredientSynonym, Category, Cuisine, Tag, BasicIngredient, UserPantry, BasicIngredientUsage # Import your models

# --- Option 1: Basic Registration ---
# This is the simplest way to get your models into the admin.
# admin.site.register(Recipe)
# admin.site.register(Ingredient)

# --- Option 2: Enhanced Registration with ModelAdmin (Recommended) ---
# Use ModelAdmin to customize how your models appear and behave in the admin.

class RecipeIngredientInline(admin.TabularInline):
    """
    Allows managing RecipeIngredient objects directly within the Recipe admin page.
    """
    model = RecipeIngredient
    extra = 1 # Number of empty forms to display for adding new ingredients
    fields = ['ingredient', 'quantity', 'unit', 'preparation'] # Show preparation notes inline


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Customizes the display of the Recipe model in the Django admin.
    """
    list_display = (
        'title',
        'contributor',
        'prep_time',
        'cook_time',
        'servings',
        'difficulty',  # Show difficulty
        'approved',  # Show approval status in the list
        'is_active',  # Show active status
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )
    list_filter = ('contributor', 'created_by', 'updated_by', 'created_at', 'updated_at', 'is_active')  # Filter by active status
    search_fields = ('title', 'description', 'instructions', 'contributor__username', 'created_by__username', 'updated_by__username') # Search by recipe fields and contributor username
    raw_id_fields = ('contributor', 'created_by', 'updated_by') # Use a raw ID input for contributor for large user bases
    date_hierarchy = 'created_at' # Add a date navigation filter
    ordering = ('-created_at',)

    # Use the inline to manage ingredients directly from the recipe form
    inlines = [RecipeIngredientInline]

    # Pre-populate slug field if you had one (e.g., from title)
    # prepopulated_fields = {'slug': ('title',)}

    # Fieldsets can group fields for better organization
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'instructions', 'contributor', 'approved', 'is_active', 'categories', 'cuisines', 'tags', 'difficulty', 'source')
        }),
        ('Details', {
            'fields': ('prep_time', 'cook_time', 'servings'),
            'classes': ('collapse',) # Makes this section collapsible
        }),
        ('Ingredients', {
            'fields': (), # Fields handled by the inline
        }),
    )

    filter_horizontal = ('categories', 'cuisines', 'tags')  # Add tags to horizontal filter

    def get_queryset(self, request):
        # Optimize query to fetch contributor data in one go
        return super().get_queryset(request).select_related('contributor')

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Customizes the display of the Ingredient model in the Django admin.
    """
    list_display = ['name', 'created_by', 'updated_by', 'created_at', 'updated_at']
    search_fields = ['name']
    list_filter = ['created_by']
    raw_id_fields = ('created_by', 'updated_by')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(BadIngredient)
class BadIngredientAdmin(admin.ModelAdmin):
    """
    Customizes the display of the BadIngredient model in the Django admin.
    """
    list_display = ('type', 'ingredients', 'description', 'created_at')
    search_fields = ('ingredients', 'description')
    list_filter = ('type', 'created_at')
    ordering = ('-created_at',)

@admin.register(IngredientSubstitution)
class IngredientSubstitutionAdmin(admin.ModelAdmin):
    """
    Customizes the display of the IngredientSubstitution model in the Django admin.
    """
    list_display = ('ingredient', 'substitutions', 'notes', 'created_at')
    search_fields = ('ingredient', 'substitutions', 'notes')
    ordering = ('ingredient',)

@admin.register(IngredientSynonym)
class IngredientSynonymAdmin(admin.ModelAdmin):
    """
    Customizes the display of the IngredientSynonym model in the Django admin.
    """
    list_display = ('name', 'ingredient')
    search_fields = ('name', 'ingredient__name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Customizes the display of the Category model in the Django admin.
    """
    list_display = ('name', 'created_at', 'updated_at', 'created_by', 'updated_by')
    list_filter = ('created_by', 'updated_by', 'created_at', 'updated_at')
    search_fields = ('name', 'created_by__username', 'updated_by__username')
    raw_id_fields = ('created_by', 'updated_by')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    """
    Customizes the display of the Cuisine model in the Django admin.
    """
    list_display = ('name', 'created_at', 'updated_at', 'created_by', 'updated_by')
    list_filter = ('created_by', 'updated_by', 'created_at', 'updated_at')
    search_fields = ('name', 'created_by__username', 'updated_by__username')
    raw_id_fields = ('created_by', 'updated_by')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Customizes the display of the Tag model in the Django admin.
    """
    list_display = ('name', 'created_at', 'updated_at', 'created_by', 'updated_by')
    list_filter = ('created_by', 'updated_by', 'created_at', 'updated_at')
    search_fields = ('name', 'created_by__username', 'updated_by__username')
    raw_id_fields = ('created_by', 'updated_by')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(BasicIngredient)
class BasicIngredientAdmin(admin.ModelAdmin):
    """
    Customizes the display of the BasicIngredient model in the Django admin.
    """
    search_fields = ['name']
    list_display = ['name', 'region']
    list_filter = ['region']

@admin.register(UserPantry)
class UserPantryAdmin(admin.ModelAdmin):
    """
    Customizes the display of the UserPantry model in the Django admin.
    """
    search_fields = ['user__username']
    list_display = ['user']
    filter_horizontal = ['ingredients']

@admin.register(BasicIngredientUsage)
class BasicIngredientUsageAdmin(admin.ModelAdmin):
    """
    Customizes the display of the BasicIngredientUsage model in the Django admin.
    """
    list_display = ['ingredient', 'user', 'region', 'timestamp']
    search_fields = ['ingredient', 'user__username', 'region']
    list_filter = ['region', 'ingredient']