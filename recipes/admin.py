from django.contrib import admin
from .models import (
    Recipe,
    Ingredient,
    RecipeIngredient,
    BadIngredient,
    IngredientSubstitution,
    IngredientSynonym,
    Category,
    Cuisine,
    Tag,
    BasicIngredient,
    UserPantry,
    BasicIngredientUsage,
    RecipeRating,
    RecipeLike,
    RecipeComment,
    LiveSession,
)  # Import your models

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

# IngredientAdmin is declared later; avoid duplicate registration.

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

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'default_unit_weight_g', 'created_by', 'updated_by', 'created_at', 'updated_at']
    list_editable = ('default_unit_weight_g',)
    search_fields = ['name']
    list_filter = ['created_by']
    raw_id_fields = ('created_by', 'updated_by')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    # Allow editing IngredientPrice inline when editing Ingredient
    # IngredientPrice is a OneToOne relation so use StackedInline with max_num=1
    class IngredientPriceInline(admin.StackedInline):
        from .models import IngredientPrice as _IP
        model = _IP
        can_delete = False
        verbose_name = 'Price (per kg)'
        verbose_name_plural = 'Price (per kg)'
        fk_name = 'ingredient'
        max_num = 1

    inlines = [IngredientPriceInline]

from .models import IngredientPrice

@admin.register(IngredientPrice)
class IngredientPriceAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'price_per_kg', 'updated_at')
    search_fields = ('ingredient__name',)
    raw_id_fields = ('ingredient',)

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

@admin.register(RecipeRating)
class RecipeRatingAdmin(admin.ModelAdmin):
    """
    Customizes the display of the RecipeRating model in the Django admin.
    """
    list_display = ['recipe', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['recipe__title', 'user__username', 'review']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(RecipeLike)
class RecipeLikeAdmin(admin.ModelAdmin):
    """
    Customizes the display of the RecipeLike model in the Django admin.
    """
    list_display = ['recipe', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['recipe__title', 'user__username']
    readonly_fields = ['created_at']

@admin.register(RecipeComment)
class RecipeCommentAdmin(admin.ModelAdmin):
    """
    Customizes the display of the RecipeComment model in the Django admin.
    """
    list_display = ['recipe', 'user', 'content', 'created_at', 'is_approved']
    list_filter = ['created_at', 'is_approved']
    search_fields = ['recipe__title', 'user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_approved']


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'provider', 'is_live', 'started_at', 'ended_at')
    list_filter = ('provider', 'is_live', 'created_at')
    search_fields = ('title', 'host__username', 'slug')
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        # If provider is set to Daily and no room is provisioned, provision it
        from recipes.views import LiveSessionViewSet
        if getattr(obj, 'provider', None) == getattr(obj, 'PROVIDER_DAILY', 'daily') and not obj.external_room_url:
            # Use the same logic as the API to provision the room
            try:
                LiveSessionViewSet._provision_external_room(LiveSessionViewSet, obj)
            except Exception as exc:
                import logging
                logging.warning(f"Daily room provisioning failed in admin: {exc}")
        super().save_model(request, obj, form, change)