from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from recipes.models import Ingredient, Recipe, RecipeIngredient, Category, Tag
import random
import decimal
from django.utils.text import slugify
from django.conf import settings
import os
import glob
from io import BytesIO
from django.core.files.base import ContentFile
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


class Command(BaseCommand):
    help = "Seed the database with programmatically generated Cameroonian recipes."

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=150, help='Number of recipes to generate')
        parser.add_argument('--username-admin', type=str, default='njoya', help='Admin username to attribute some recipes')
        parser.add_argument('--username-contrib', type=str, default='precious', help='Contributor username to attribute some recipes')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be created without writing')
        parser.add_argument('--yes', action='store_true', help='Apply changes without interactive confirmation')
        parser.add_argument('--images-dir', type=str, help='Optional path to a directory of images to attach to recipes')

    SAMPLE_DISHES = [
        'Ndolé', 'Achu', 'Eru', 'Fufu', 'Koki', 'Poulet DG', 'Egusi stew', 'Okra soup',
        'Kondreh', 'Mbongo Tchobi', 'Poisson braisé', 'Pepper soup', 'Kili-kili (grilled corn)',
        'Garri with stew', 'Plantain pottage', 'Bongo meat', 'Afang', 'Bitterleaf stew',
        'Beans and plantain', 'Jollof rice (Cameroonian style)', 'White rice with stew',
        'Cassava leaf stew', 'Brochettes (skewers)', 'Sanga (stewed beef with plantain)',
        'Ndolé with shrimp', 'Palm nut soup', 'Koki corn', 'Koki beans', 'Achomo (stewed fish)'
    ]

    ADJECTIVES = ['classic', 'spicy', 'smoky', 'creamy', 'rustic', 'quick', 'hearty', 'comfort']

    def _pick_ingredients(self, ingredients_qs, needed=8):
        # Prefer staples and proteins when available
        pool = list(ingredients_qs)
        if not pool:
            return []
        picked = set()
        attempts = 0
        while len(picked) < needed and attempts < needed * 5:
            picked.add(random.choice(pool))
            attempts += 1
        return list(picked)

    def _estimate_cost(self, ingredients):
        # heuristic cost per ingredient category guess; return Decimal (francs)
        base_prices = {
            'Staple': 800, 'Protein': 1200, 'Vegetable': 400, 'Spice': 100, 'Pantry': 300, 'Oil': 250
        }
        total = 0
        for ing in ingredients:
            # naive category inference by checking ingredient name keywords
            name = ing.name.lower()
            if any(x in name for x in ['rice', 'fufu', 'cassava', 'garri', 'maize', 'corn', 'plantain', 'yam', 'cassava']):
                total += base_prices.get('Staple', 500)
            elif any(x in name for x in ['beef', 'chicken', 'fish', 'pork', 'goat', 'shrimp', 'prawns', 'eggs']):
                total += base_prices.get('Protein', 1000)
            elif any(x in name for x in ['oil', 'butter']):
                total += base_prices.get('Oil', 300)
            elif any(x in name for x in ['salt', 'sugar', 'stock', 'tomato', 'sauce', 'paste']):
                total += base_prices.get('Pantry', 250)
            elif any(x in name for x in ['pepper', 'ginger', 'garlic', 'curry', 'clove', 'paprika']):
                total += base_prices.get('Spice', 120)
            else:
                total += 350
        # scale down to represent a meal serving for 4
        est = decimal.Decimal(total) / decimal.Decimal(4)
        # round to 2 decimals
        return est.quantize(decimal.Decimal('1.'), rounding=decimal.ROUND_HALF_UP)

    def _make_instructions(self, ingredients):
        lines = []
        lines.append('Prep: wash and chop vegetables and season proteins.')
        lines.append('Heat oil in a pot, sauté aromatics, add proteins and brown lightly.')
        lines.append('Add staples and liquids, simmer until cooked and flavors develop.')
        lines.append('Adjust seasoning with salt and stock cube as needed. Serve hot.')
        return '\n'.join(lines)

    def _ensure_verified(self, user, verified_by_user=None):
        """Mark a user as a verified contributor if not already."""
        if not getattr(user, 'is_verified_contributor', False):
            user.is_verified_contributor = True
            import django.utils.timezone as timezone
            user.verified_at = timezone.now()
            user.verified_by = verified_by_user
            user.save()

    def _generate_image(self, title, slug):
        """Generate a placeholder image for the recipe and return ContentFile bytes."""
        # If PIL is not installed, return None and skip image attachment
        if not PIL_AVAILABLE:
            return None

        WIDTH, HEIGHT = 1200, 800
        bg_color = (230, 180, 120)
        img = Image.new('RGB', (WIDTH, HEIGHT), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Load a default font; truetype may not be available in all envs
        try:
            font = ImageFont.truetype('arial.ttf', 48)
        except Exception:
            font = ImageFont.load_default()

        # Draw title centered
        lines = [title]
        y = HEIGHT // 2 - 20
        for line in lines:
            # Prefer font.getsize, fall back to ImageDraw.textbbox, else approximate
            try:
                w, h = font.getsize(line)
            except Exception:
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                except Exception:
                    w, h = (len(line) * 20, 50)
            draw.text(((WIDTH - w) / 2, y), line, fill=(30, 30, 30), font=font)
            y += h + 5

        # Save to bytes
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=85)
        buf.seek(0)
        return ContentFile(buf.read(), name=f'{slug}.jpg')

    def handle(self, *args, **options):
        count = options['count']
        dry_run = options['dry_run']
        yes = options['yes']
        admin_username = options['username_admin']
        contrib_username = options['username_contrib']

        User = get_user_model()
        admin = User.objects.filter(username=admin_username).first()
        contrib = User.objects.filter(username=contrib_username).first()
        if not admin or not contrib:
            self.stdout.write(self.style.ERROR(f"Ensure users '{admin_username}' and '{contrib_username}' exist before running this command."))
            return

        # Ensure both users are verified contributors
        self._ensure_verified(admin, verified_by_user=admin)
        self._ensure_verified(contrib, verified_by_user=admin)

        ingredients_qs = list(Ingredient.objects.all())
        if not ingredients_qs:
            self.stdout.write(self.style.ERROR('No ingredients found in DB. Run seed_cameroon first.'))
            return
        images_dir = options.get('images_dir')
        image_files = []
        if images_dir:
            # Resolve relative to project root if needed
            if not os.path.isabs(images_dir):
                images_dir = os.path.abspath(images_dir)
            if os.path.isdir(images_dir):
                # collect common image extensions
                for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
                    image_files.extend(glob.glob(os.path.join(images_dir, ext)))
                if not image_files:
                    self.stdout.write(self.style.WARNING(f'No image files found in {images_dir}; falling back to generated placeholders.'))
            else:
                self.stdout.write(self.style.WARNING(f'Images directory {images_dir} not found; falling back to generated placeholders.'))

        self.stdout.write(f'Will generate {count} recipes (dry_run={dry_run})')
        if not dry_run and not yes:
            confirm = input('Proceed to create recipes? Type YES to continue: ')
            if confirm.strip() != 'YES':
                self.stdout.write('Aborted.')
                return

        created = 0
        skipped = 0
        for i in range(count):
            base = random.choice(self.SAMPLE_DISHES)
            adjective = random.choice(self.ADJECTIVES)
            title = f"{base} ({adjective})" if random.random() < 0.6 else f"{base}"
            # make title unique-ish
            if Recipe.objects.filter(title__iexact=title).exists():
                title = f"{title} - {i}"

            picked = self._pick_ingredients(ingredients_qs, needed=random.randint(5, 10))
            if not picked:
                skipped += 1
                continue

            est_cost = self._estimate_cost(picked)
            prep = random.randint(10, 40)
            cook = random.randint(15, 90)
            servings = random.choice([2, 4, 6])
            instructions = self._make_instructions(picked)
            description = f"A {adjective} preparation of {base}, a Cameroonian dish. Serves {servings}."

            # alternate contributor assignment
            contributor = admin if i % 3 == 0 else contrib

            if dry_run:
                created += 1
                continue

            # create recipe and ingredients inside a transaction
            try:
                with transaction.atomic():
                    recipe = Recipe.objects.create(
                        title=title,
                        description=description,
                        instructions=instructions,
                        prep_time=prep,
                        cook_time=cook,
                        servings=servings,
                        estimated_cost=est_cost,
                        contributor=contributor,
                        created_by=contributor,
                        updated_by=contributor,
                    )
                    # Attach an image: prefer a file from --images-dir, otherwise generate placeholder
                    slug = getattr(recipe, 'slug', slugify(title))
                    if image_files:
                        import random as _rand
                        imgpath = _rand.choice(image_files)
                        try:
                            # read bytes and attach using original filename
                            with open(imgpath, 'rb') as _f:
                                data = _f.read()
                            name = os.path.basename(imgpath)
                            recipe.image.save(name, ContentFile(data), save=True)
                        except Exception:
                            # fallback to generated placeholder if attaching fails
                            image_file = self._generate_image(title, slug)
                            if image_file:
                                try:
                                    recipe.image.save(image_file.name, image_file, save=True)
                                except Exception:
                                    pass
                    else:
                        image_file = self._generate_image(title, slug)
                        if image_file:
                            try:
                                recipe.image.save(image_file.name, image_file, save=True)
                            except Exception:
                                # Ignore image save failures but continue
                                pass
                    # attach some categories/tags if present
                    # add a tag for the base dish
                    tag, _ = Tag.objects.get_or_create(name=base)
                    recipe.tags.add(tag)

                    for idx, ing in enumerate(picked):
                        qty = round(random.uniform(0.1, 1.0) * (100 if idx % 2 == 0 else 200), 1)
                        unit = 'g'
                        RecipeIngredient.objects.create(recipe=recipe, ingredient=ing, quantity=qty, unit=unit)

                    created += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to create recipe "{title}": {e}'))
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f'Seeding complete. Created: {created}, Skipped: {skipped}'))
