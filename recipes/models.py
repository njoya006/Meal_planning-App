"""Recipe models for the ChopSmo application."""

from django.conf import settings
from django.db import models
from django.db.models import Sum, F
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Ingredient(models.Model):
    """Model representing a recipe ingredient."""
    
    name = models.CharField(max_length=100, unique=True, help_text="Ingredient name.")
    calories_per_100g = models.FloatField(
        _('Calories per 100g'), 
        default=0, 
        help_text=_('Calories per 100g')
    )
    # Estimated grams per single non-weight unit (e.g., grams per piece or per cup)
    default_unit_weight_g = models.FloatField(
        _('Default unit weight (g)'),
        null=True,
        blank=True,
        help_text=_('Default grams for a single unit (e.g., grams per piece or per cup) used for cost estimation of non-weight units')
    )
    protein_per_100g = models.FloatField(
        _('Protein per 100g (g)'), 
        default=0, 
        help_text=_('Protein per 100g (g)')
    )
    fat_per_100g = models.FloatField(
        _('Fat per 100g (g)'), 
        default=0, 
        help_text=_('Fat per 100g (g)')
    )
    carbs_per_100g = models.FloatField(
        _('Carbs per 100g (g)'), 
        default=0, 
        help_text=_('Carbs per 100g (g)')
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ingredients_created',
        help_text=_('User who originally created this ingredient.')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ingredients_updated',
        help_text=_('User who last updated this ingredient.')
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"

    def save(self, *args, **kwargs):
        """Save ingredient with audit fields."""
        user = kwargs.pop('user', None)
        if not self.pk and not self.created_by:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    """Model representing a recipe category."""
    
    name = models.CharField(_('Name'), max_length=100, unique=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_created',
        help_text=_('User who originally created this category.')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_updated',
        help_text=_('User who last updated this category.')
    )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not self.pk and not self.created_by:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Cuisine(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuisines_created',
        help_text=_('User who originally created this cuisine.')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuisines_updated',
        help_text=_('User who last updated this cuisine.')
    )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not self.pk and not self.created_by:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(_('Name'), max_length=50, unique=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tags_created',
        help_text=_('User who originally created this tag.')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tags_updated',
        help_text=_('User who last updated this tag.')
    )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not self.pk and not self.created_by:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

DIFFICULTY_CHOICES = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]

UNIT_CHOICES = [
    ('g', 'grams'),
    ('kg', 'kilograms'),
    ('mg', 'milligrams'),
    ('lb', 'pounds'),
    ('oz', 'ounces'),
    ('ml', 'milliliters'),
    ('l', 'liters'),
    ('cup', 'cup'),
    ('tbsp', 'tablespoon'),
    ('tsp', 'teaspoon'),
    ('piece', 'piece'),
    ('slice', 'slice'),
    ('clove', 'clove'),
    ('cloves', 'cloves'),
    ('pinch', 'pinch'),
    ('dash', 'dash'),
    ('handful', 'handful'),
    ('bunch', 'bunch'),
    ('can', 'can'),
    ('bottle', 'bottle'),
    ('package', 'package'),
    # Add more as needed
]

class Recipe(models.Model):
    estimated_cost = models.DecimalField(_('Estimated Cost'), max_digits=8, decimal_places=2, null=True, blank=True, help_text=_('Estimated total cost of ingredients for this recipe in francs'))
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=_('Contributor')
    )
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'))
    instructions = models.TextField(_('Instructions'))
    prep_time = models.IntegerField(_('Preparation time (minutes)'), help_text=_('Preparation time in minutes'), null=True, blank=True)
    cook_time = models.IntegerField(_('Cook time (minutes)'), help_text=_('Cook time in minutes'), null=True, blank=True)
    servings = models.IntegerField(_('Servings'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    approved = models.BooleanField(_('Approved'), default=False)
    feedback = models.TextField(_('Feedback'), blank=True, null=True)
    difficulty = models.CharField(_('Difficulty'), max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    source = models.CharField(_('Source/Credit'), max_length=255, blank=True, help_text=_('Recipe source or credit'))
    image = models.ImageField(_('Image'), upload_to='recipes/images/', null=True, blank=True)
    slug = models.SlugField(_('Slug'), max_length=255, unique=True, blank=True)
    is_active = models.BooleanField(_('Is active'), default=True, help_text=_('Soft delete: uncheck to hide recipe without removing from DB'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipes_created',
        help_text=_('User who originally created this recipe.'),
        verbose_name=_('Created by')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipes_updated',
        help_text=_('User who last updated this recipe.'),
        verbose_name=_('Updated by')
    )

    # Many-to-many relationship with Ingredient through RecipeIngredient
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes_used_in'
    )
    categories = models.ManyToManyField('Category', blank=True, related_name='recipes')
    cuisines = models.ManyToManyField('Cuisine', blank=True, related_name='recipes')
    tags = models.ManyToManyField('Tag', blank=True, related_name='recipes')    # You could also add fields like:
    # dietary_preferences = models.ManyToManyField(DietaryPreference, blank=True) # if you link to users.DietaryPreference

    def __str__(self):
        return self.title

    def _generate_unique_slug(self):
        """Generate a unique slug for the recipe."""
        base_slug = slugify(self.title)
        unique_slug = base_slug
        counter = 1
        
        while Recipe.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        
        return unique_slug

    def save(self, *args, **kwargs):
        # Accept a special kwarg: user
        user = kwargs.pop('user', None)
        if not self.pk and not self.created_by:
            self.created_by = user
        if user:
            self.updated_by = user
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def calculate_nutrition(self):
        """
        Calculate the total nutrition for this recipe based on its ingredients and their quantities/units.
        Assumes each Ingredient has nutrition info per 100g or per unit (extend Ingredient model as needed).
        Returns a dict with total calories, protein, fat, carbs, etc.
        """
        nutrition = {'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0}
        for ri in self.recipeingredient_set.select_related('ingredient').all():
            ing = ri.ingredient
            # Assume Ingredient model has nutrition fields per 100g or per unit
            # e.g., ing.calories_per_100g, ing.protein_per_100g, etc.
            # You may need to add these fields to Ingredient if not present
            qty = ri.quantity
            unit = ri.unit.lower()
            # For now, assume all units are grams (extend logic for cups, tbsp, etc.)
            factor = qty / 100.0  # if per 100g
            nutrition['calories'] += getattr(ing, 'calories_per_100g', 0) * factor
            nutrition['protein'] += getattr(ing, 'protein_per_100g', 0) * factor
            nutrition['fat'] += getattr(ing, 'fat_per_100g', 0) * factor
            nutrition['carbs'] += getattr(ing, 'carbs_per_100g', 0) * factor
        return nutrition

    @property
    def average_rating(self):
        """Calculate and return the average rating for this recipe."""
        ratings = self.rating_set.all()
        if not ratings:
            return None
        return sum(r.rating for r in ratings) / len(ratings)
    
    @property
    def rating_count(self):
        """Return the number of ratings for this recipe."""
        return self.rating_set.count()
    
    @property
    def like_count(self):
        """Return the number of likes for this recipe."""
        # Use the relationship field for actual count
        return self.like_set.count()
    
    @property
    def comment_count(self):
        """Return the number of comments for this recipe."""
        # Use the relationship field for actual count
        return self.comment_set.filter(is_approved=True).count()
        
    def update_counters(self):
        """Update the counter fields with the actual counts."""
        self.views = self.views or 0  # Keep the existing view count
        self.likes = self.like_set.count()
        self.comments = self.comment_set.filter(is_approved=True).count()
        self.saves = self.saves or 0   # Keep the existing save count
        self.save(update_fields=['views', 'likes', 'comments', 'saves'])


class RecipeImage(models.Model):
    """Allow multiple images per recipe. Kept simple and ordered."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='recipes/images/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(default=0, help_text='Ordering for gallery images')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_recipe_images'
    )

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.recipe.title} (#{self.order})"


class InstructionStepImage(models.Model):
    """Optional image attached to a specific instruction step in a recipe.

    Since instructions are stored as free text, we attach the image to a step_index
    (1-based) so the frontend can map images to steps when rendering.
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='step_images')
    step_index = models.PositiveIntegerField(help_text='1-based instruction step index')
    image = models.ImageField(upload_to='recipes/steps/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_step_images'
    )

    class Meta:
        unique_together = ('recipe', 'step_index')
        ordering = ['step_index']

    def __str__(self):
        return f"Step {self.step_index} image for {self.recipe.title}"

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField() # e.g., 2.5
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    preparation = models.CharField(max_length=255, blank=True, help_text="Preparation notes (e.g., diced, thinly sliced)")

    class Meta:
        unique_together = ('recipe', 'ingredient') # An ingredient should only appear once per recipe

    def __str__(self):
        prep = f", {self.preparation}" if self.preparation else ""
        return f"{self.quantity} {self.unit}{prep} of {self.ingredient.name} in {self.recipe.title}"

class BadIngredient(models.Model):
    INGREDIENT_TYPE_CHOICES = [
        ("pair", "Pair"),
        ("combination", "Combination"),
        ("category", "Category"),
    ]
    ingredients = models.JSONField(help_text="List of ingredient names (lowercase)")
    type = models.CharField(max_length=20, choices=INGREDIENT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type}: {', '.join(self.ingredients)}"

class IngredientSubstitution(models.Model):
    ingredient = models.CharField(max_length=100, help_text="Ingredient to substitute (lowercase)")
    substitutions = models.JSONField(help_text="List of possible substitutions (lowercase)")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ingredient} → {', '.join(self.substitutions)}"

class IngredientSynonym(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='synonyms')
    name = models.CharField(max_length=100, unique=True, help_text="Synonym or variation name (e.g., 'Coriander', 'Tomatoes')")

    def __str__(self):
        return f"{self.name} (synonym for {self.ingredient.name})"

class BasicIngredient(models.Model):
    REGION_CHOICES = [
        ('global', 'Global'),
        ('us', 'United States'),
        ('uk', 'United Kingdom'),
        ('fr', 'France'),
        ('ng', 'Nigeria'),
        ('in', 'India'),
        # Add more as needed
    ]
    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=10, choices=REGION_CHOICES, default='global', help_text="Region/culture for this basic ingredient list.")

    class Meta:
        verbose_name = "Basic Ingredient"
        verbose_name_plural = "Basic Ingredients"
        ordering = ['region', 'name']

    def __str__(self):
        return f"{self.name} ({self.region})"


class IngredientPrice(models.Model):
    """Optional per-ingredient price (per kilogram) for more accurate cost estimates."""
    ingredient = models.OneToOneField(Ingredient, on_delete=models.CASCADE, related_name='price')
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price per kilogram in local currency (e.g., CFA)')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ingredient.name}: {self.price_per_kg} per kg"

class UserPantry(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pantry')
    ingredients = models.ManyToManyField('Ingredient', blank=True, help_text="Ingredients this user always has available.")

    def __str__(self):
        return f"{self.user.username}'s Pantry"

class BasicIngredientUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    ingredient = models.CharField(max_length=100)
    region = models.CharField(max_length=10, default='global')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.ingredient} (user: {self.user}, region: {self.region}, {self.timestamp})"

class RecipeRating(models.Model):
    """Model representing a user's rating and optional review for a recipe."""
    
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ]
    
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='rating_set',
        verbose_name=_('Recipe')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipe_ratings',
        verbose_name=_('User')
    )
    rating = models.PositiveSmallIntegerField(
        _('Rating'),
        choices=RATING_CHOICES,
        help_text=_('Rating from 1 to 5 stars')
    )
    review = models.TextField(
        _('Review'),
        blank=True,
        null=True,
        help_text=_('Optional review text')
    )
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        verbose_name = _('Recipe Rating')
        verbose_name_plural = _('Recipe Ratings')
        # Ensure a user can only rate a recipe once
        unique_together = ('recipe', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s {self.rating}-star rating for {self.recipe.title}"

class RecipeLike(models.Model):
    """Model representing a user's like for a recipe."""
    
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='like_set',
        verbose_name=_('Recipe')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipe_likes',
        verbose_name=_('User')
    )
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Recipe Like')
        verbose_name_plural = _('Recipe Likes')
        # Ensure a user can only like a recipe once
        unique_together = ('recipe', 'user')

    def __str__(self):
        return f"{self.user.username} likes {self.recipe.title}"


class RecipeComment(models.Model):
    """Model representing a user's comment on a recipe."""
    
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='comment_set',
        verbose_name=_('Recipe')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipe_comments',
        verbose_name=_('User')
    )
    content = models.TextField(_('Comment'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    is_approved = models.BooleanField(_('Approved'), default=True, help_text=_('Comment requires approval before being shown publicly'))

    class Meta:
        verbose_name = _('Recipe Comment')
        verbose_name_plural = _('Recipe Comments')
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.recipe.title}"


# --- Live streaming MVP models ---
class LiveSession(models.Model):
    """Represents a live cooking session started by a verified contributor.

    Note: This model only stores metadata and control flags. Actual video
    streaming should use a media server (RTMP/WebRTC) or third-party provider.
    """
    PROVIDER_LOCAL = 'local'
    PROVIDER_DAILY = 'daily'
    PROVIDER_CHOICES = [
        (PROVIDER_LOCAL, 'Local'),
        (PROVIDER_DAILY, 'Daily'),
    ]

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='live_sessions'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_live = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    # Random stream key for RTMP/ingest identification; regenerate as needed
    stream_key = models.CharField(max_length=64, unique=True, blank=True)
    viewer_count = models.IntegerField(default=0)
    provider = models.CharField(
        max_length=32,
        choices=PROVIDER_CHOICES,
        default=PROVIDER_LOCAL,
        help_text='Streaming backend powering this live session.'
    )
    external_room_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Identifier for the external streaming room (e.g., Daily room name).'
    )
    external_room_url = models.URLField(
        blank=True,
        help_text='Join URL provided by the external streaming provider.'
    )
    external_room_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Raw provisioning payload returned by the streaming provider.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Live: {self.title} by {self.host.username}"

    def save(self, *args, **kwargs):
        # Create a simple stream_key if not provided
        if not self.stream_key:
            import secrets
            self.stream_key = secrets.token_urlsafe(32)
        if not self.slug:
            base = slugify(self.title)[:200]
            unique = base
            counter = 1
            while LiveSession.objects.filter(slug=unique).exclude(pk=self.pk).exists():
                unique = f"{base}-{counter}"
                counter += 1
            self.slug = unique
        super().save(*args, **kwargs)


class LiveChatMessage(models.Model):
    """Simple chat message attached to a LiveSession. For real-time chat, use Django Channels or a managed WebSocket service."""
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.message[:40]}"


class WebsocketToken(models.Model):
    """Ephemeral token issued for authenticating a single websocket connection.

    The token contains a jti and is marked used after one successful connection.
    """
    jti = models.CharField(max_length=128, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ws_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"WS token {self.jti} for {self.user.username} (used={self.used})"