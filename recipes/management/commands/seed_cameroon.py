from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
import json
import csv
from pathlib import Path

from recipes.models import (
    Ingredient,
    Category,
    Cuisine,
    Tag,
    BasicIngredient,
    IngredientSynonym,
    IngredientSubstitution,
    BadIngredient,
)


CAMEROON_DATA = {
    "cuisines": ["Cameroonian"],
    "categories": [
        "Staple",
        "Vegetable",
        "Protein",
        "Spice",
        "Oil",
        "Seafood",
        "Legume",
        "Fruit",
    ],
    "tags": ["stew", "soup", "staple", "vegetarian", "vegan", "gluten-free", "spicy"],
    "basic_ingredients": [
        {"name": "Cassava", "region": "cm"},
        {"name": "Plantain", "region": "cm"},
        {"name": "Yam", "region": "cm"},
        {"name": "Maize", "region": "cm"},
        {"name": "Rice", "region": "cm"},
        {"name": "Palm oil", "region": "cm"},
    ],
    "ingredients": [
        {
            "name": "Cassava",
            "synonyms": ["Manioc", "Tapioca"],
            "substitutions": ["Yam", "Plantain"],
            "categories": ["Staple"],
            "tags": ["staple", "gluten-free"]
        },
        {
            "name": "Plantain",
            "synonyms": ["Cooking banana"],
            "substitutions": ["Banana (ripe)", "Cassava"],
            "categories": ["Staple", "Fruit"],
            "tags": ["staple"]
        },
        {
            "name": "Yam",
            "synonyms": [],
            "substitutions": ["Cassava"],
            "categories": ["Staple"],
            "tags": ["staple"]
        },
        {
            "name": "Maize",
            "synonyms": ["Corn"],
            "substitutions": [],
            "categories": ["Staple"],
            "tags": ["staple"]
        },
        {
            "name": "Okra",
            "synonyms": ["Lady's finger"],
            "substitutions": [],
            "categories": ["Vegetable"],
            "tags": ["soup", "vegetarian"]
        },
        {
            "name": "Palm oil",
            "synonyms": ["Red palm oil"],
            "substitutions": ["Vegetable oil"],
            "categories": ["Oil"],
            "tags": ["stew"]
        },
        {
            "name": "Groundnut",
            "synonyms": ["Peanut"],
            "substitutions": [],
            "categories": ["Legume", "Protein"],
            "tags": ["stew", "protein"]
        },
        {
            "name": "Smoked fish",
            "synonyms": [],
            "substitutions": ["Dried fish"],
            "categories": ["Seafood", "Protein"],
            "tags": ["stew"]
        },
        {
            "name": "Crayfish",
            "synonyms": ["Dried shrimp"],
            "substitutions": [],
            "categories": ["Seafood"],
            "tags": ["stew", "soup"]
        },
        {
            "name": "Tomato",
            "synonyms": ["Tomatoes"],
            "substitutions": [],
            "categories": ["Vegetable"],
            "tags": ["stew", "soup"]
        },
        {
            "name": "Onion",
            "synonyms": [],
            "substitutions": [],
            "categories": ["Vegetable"],
            "tags": ["stew", "soup"]
        },
        {
            "name": "Garlic",
            "synonyms": [],
            "substitutions": [],
            "categories": ["Spice"],
            "tags": ["stew"]
        },
        {
            "name": "Ginger",
            "synonyms": [],
            "substitutions": [],
            "categories": ["Spice"],
            "tags": ["stew"]
        },
        {
            "name": "Chili pepper",
            "synonyms": ["Hot pepper"],
            "substitutions": [],
            "categories": ["Spice"],
            "tags": ["spicy"]
        },
        {
            "name": "Eggplant (garden egg)",
            "synonyms": ["Garden egg"],
            "substitutions": ["Aubergine"],
            "categories": ["Vegetable"],
            "tags": ["stew"]
        },
        {
            "name": "Bambara groundnut",
            "synonyms": [],
            "substitutions": ["Peanut", "Cowpea"],
            "categories": ["Legume"],
            "tags": ["protein"]
        },
        {
            "name": "Cowpea",
            "synonyms": ["Black-eyed pea"],
            "substitutions": [],
            "categories": ["Legume", "Protein"],
            "tags": ["stew", "protein"]
        },
        {
            "name": "Spinach (cassava leaves)",
            "synonyms": ["Cassava leaves"],
            "substitutions": ["Spinach"],
            "categories": ["Vegetable"],
            "tags": ["soup", "vegetarian"]
        },
        {
            "name": "Rice",
            "synonyms": ["White rice", "Broken rice"],
            "substitutions": ["Maize (corn)", "Cassava"],
            "categories": ["Staple"],
            "tags": ["staple"]
        },
        {
            "name": "Chicken",
            "synonyms": ["Poulet"],
            "substitutions": ["Beef", "Fish"],
            "categories": ["Protein"],
            "tags": ["stew", "protein"]
        },
        {
            "name": "Beef",
            "synonyms": [],
            "substitutions": ["Chicken"],
            "categories": ["Protein"],
            "tags": ["stew"]
        },
        {
            "name": "Fish (fresh)",
            "synonyms": ["Fresh fish"],
            "substitutions": ["Smoked fish", "Dried fish"],
            "categories": ["Seafood", "Protein"],
            "tags": ["stew", "grill"]
        },
        {
            "name": "Dried fish",
            "synonyms": [],
            "substitutions": ["Smoked fish"],
            "categories": ["Seafood"],
            "tags": ["stew"]
        },
        {
            "name": "Tomato paste",
            "synonyms": ["Concentrated tomato"],
            "substitutions": ["Tomato"],
            "categories": ["Pantry"],
            "tags": ["stew"]
        },
        {
            "name": "Bitterleaf",
            "synonyms": [],
            "substitutions": ["Spinach"],
            "categories": ["Vegetable"],
            "tags": ["soup"]
        },
        {
            "name": "Garden egg (small eggplant)",
            "synonyms": ["Garden egg", "Small eggplant"],
            "substitutions": ["Eggplant (garden egg)"],
            "categories": ["Vegetable"],
            "tags": ["stew"]
        },
    ]
}


class Command(BaseCommand):
    help = "Seed the database with an initial set of Cameroon ingredients, categories, tags, cuisines, synonyms and substitutions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            help="Username to set as created_by/updated_by on created objects (optional).",
        )
        parser.add_argument(
            "--file",
            help="Path to a JSON or CSV file containing the data to import. If omitted, built-in CAMEROON_DATA is used.",
        )
        parser.add_argument(
            "--format",
            choices=["json", "csv"],
            help="Format of the input file (json or csv). If omitted will be inferred from filename extension.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry-run: report what would be created without writing to the database.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip interactive confirmation prompt and proceed to write to the database (use carefully).",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options.get("username")
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' does not exist")

    input_file = options.get("file")
    input_format = options.get("format")
    dry_run = bool(options.get("dry_run"))
    assume_yes = bool(options.get("yes"))

        # If file provided, try to load it and merge into data
        data = CAMEROON_DATA.copy()
        if input_file:
            data = self._load_input_file(Path(input_file), input_format) or data

        created = {"cuisines": 0, "categories": 0, "tags": 0, "basic_ingredients": 0, "ingredients": 0, "synonyms": 0, "substitutions": 0}

        # Use transaction when not a dry run; when dry-run we still query existence but avoid writes
        atomic_ctx = transaction.atomic() if not dry_run else (lambda: (yield))

        # Helper to either create-or-get or only check existence when dry-run
        def _ensure(model, lookup, defaults=None, set_user=False, count_key=None):
            """Ensure an object exists. If dry_run, only check and increment counts; otherwise perform get_or_create and optionally set created_by."""
            nonlocal created
            defaults = defaults or {}
            if dry_run:
                exists = model.objects.filter(**lookup).exists()
                if not exists and count_key:
                    created[count_key] += 1
                return None, (not exists)
            else:
                obj, created_flag = model.objects.get_or_create(**lookup, defaults=defaults)
                if created_flag and count_key:
                    created[count_key] += 1
                if set_user and obj and user:
                    obj.created_by = user
                    obj.updated_by = user
                    obj.save()
                return obj, created_flag

        # If we're going to write to the DB, require explicit confirmation unless --yes was provided
        if not dry_run and not assume_yes:
            self.stdout.write(self.style.WARNING("About to write changes to the database."))
            confirm = input("Type YES to proceed: ").strip()
            if confirm != "YES":
                raise CommandError("Aborted by user.")

        # Enter transaction when writing
        if not dry_run:
            tx = transaction.atomic()
        else:
            # dummy context manager
            from contextlib import nullcontext
            tx = nullcontext()

        with tx:
            # Cuisines
            for cname in data.get("cuisines", []):
                _obj, created_flag = _ensure(Cuisine, {"name": cname}, set_user=True, count_key="cuisines")

            # Categories
            for cat in data.get("categories", []):
                _obj, created_flag = _ensure(Category, {"name": cat}, set_user=True, count_key="categories")

            # Tags
            for t in data.get("tags", []):
                _obj, created_flag = _ensure(Tag, {"name": t}, set_user=True, count_key="tags")

            # Basic Ingredients
            for b in data.get("basic_ingredients", []):
                name = b.get("name") if isinstance(b, dict) else b
                defaults = {"region": b.get("region", "global")} if isinstance(b, dict) else {}
                _obj, created_flag = _ensure(BasicIngredient, {"name": name}, defaults=defaults, count_key="basic_ingredients")

            # Ingredients and related records
            for item in data.get("ingredients", []):
                name = item.get("name")
                ing_obj, created_flag = _ensure(Ingredient, {"name": name}, set_user=True, count_key="ingredients")

                # if dry-run, ing_obj will be None; fetch a reference if needed for related records
                if not ing_obj:
                    try:
                        ing_obj = Ingredient.objects.filter(name=name).first()
                    except Exception:
                        ing_obj = None

                # categories - only ensure category exists; linking to recipes handled elsewhere
                for cat_name in item.get("categories", []):
                    if not Category.objects.filter(name=cat_name).exists():
                        self.stdout.write(self.style.WARNING(f"Category '{cat_name}' not found for ingredient {name}"))

                # tags - ensure exist
                for tag_name in item.get("tags", []):
                    _obj, _created = _ensure(Tag, {"name": tag_name}, count_key="tags")

                # synonyms
                for syn in item.get("synonyms", []):
                    syn_name = syn.strip()
                    if not syn_name:
                        continue
                    if dry_run:
                        exists = IngredientSynonym.objects.filter(ingredient__name=name, name=syn_name).exists()
                        if not exists:
                            created["synonyms"] += 1
                    else:
                        syn_obj, syn_created = IngredientSynonym.objects.get_or_create(ingredient=ing_obj, name=syn_name)
                        if syn_created:
                            created["synonyms"] += 1

                # substitutions (store as IngredientSubstitution entries)
                subs = item.get("substitutions", [])
                if subs:
                    ing_key = name.lower()
                    if dry_run:
                        exists = IngredientSubstitution.objects.filter(ingredient=ing_key).exists()
                        if not exists:
                            created["substitutions"] += 1
                    else:
                        sub_obj, sub_created = IngredientSubstitution.objects.get_or_create(
                            ingredient=ing_key,
                            defaults={"substitutions": [s.lower() for s in subs]}
                        )
                        if not sub_created:
                            # Merge substitutions if needed
                            existing = sub_obj.substitutions or []
                            merged = list({*existing, *[s.lower() for s in subs]})
                            if merged != existing:
                                sub_obj.substitutions = merged
                                sub_obj.save()
                        else:
                            created["substitutions"] += 1

            # Seed BadIngredient examples (pairs/categories)
            # Note: BadIngredient model uses a JSONField 'ingredients' and 'type'.
            # We'll add a few defensive examples commonly considered incompatible.
            try:
                # Pair example: milk and fish often avoided together in some traditions
                if dry_run:
                    if not BadIngredient.objects.filter(type='pair', ingredients__contains=['milk', 'fish']).exists():
                        created.setdefault('bad_ingredients', 0)
                        created['bad_ingredients'] += 1
                else:
                    bi, bi_created = BadIngredient.objects.get_or_create(
                        type='pair',
                        defaults={'ingredients': ['milk', 'fish'], 'description': 'milk-fish pair'}
                    )
                    if bi_created:
                        created.setdefault('bad_ingredients', 0)
                        created['bad_ingredients'] += 1

                # Category example: example category 'oil-sensitive' listing ingredients to avoid
                if dry_run:
                    if not BadIngredient.objects.filter(type='category', description__icontains='oil-sensitive').exists():
                        created.setdefault('bad_ingredients', 0)
                        created['bad_ingredients'] += 1
                else:
                    bc, bc_created = BadIngredient.objects.get_or_create(
                        type='category',
                        defaults={'ingredients': ['palm oil'], 'description': 'oil-sensitive'}
                    )
                    if bc_created:
                        created.setdefault('bad_ingredients', 0)
                        created['bad_ingredients'] += 1
            except Exception:
                # If BadIngredient model is not available or migration mismatch, skip gracefully
                pass

        # Summary
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: no database writes were performed."))
        else:
            self.stdout.write(self.style.SUCCESS("Seeding completed."))

        for k, v in created.items():
            self.stdout.write(f"{k}: {v}")

    def _load_input_file(self, path: Path, fmt: str | None):
        """Load JSON or CSV file and return a dict matching CAMEROON_DATA structure.

        JSON file is expected to already match CAMEROON_DATA shape. CSV should have a 'type' column
        with values like 'ingredient','basic','category','tag','cuisine' and additional fields.
        """
        if not path.exists():
            raise CommandError(f"Input file {path} does not exist")

        inferred = fmt or (path.suffix.lstrip('.').lower() or 'json')
        if inferred == 'json':
            with path.open('r', encoding='utf-8') as fh:
                try:
                    obj = json.load(fh)
                    return obj
                except json.JSONDecodeError as e:
                    raise CommandError(f"Invalid JSON file: {e}")

        if inferred == 'csv':
            out = {"cuisines": [], "categories": [], "tags": [], "basic_ingredients": [], "ingredients": []}
            with path.open('r', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    rtype = (row.get('type') or '').strip().lower()
                    name = (row.get('name') or '').strip()
                    if not rtype or not name:
                        continue
                    if rtype in ('cuisine', 'cuisines'):
                        out['cuisines'].append(name)
                    elif rtype in ('category', 'categories'):
                        out['categories'].append(name)
                    elif rtype in ('tag', 'tags'):
                        out['tags'].append(name)
                    elif rtype in ('basic', 'basic_ingredient', 'basic_ingredients'):
                        out['basic_ingredients'].append({'name': name, 'region': row.get('region', '').strip() or 'cm'})
                    elif rtype in ('ingredient', 'ingredients'):
                        item = {'name': name}
                        # optional pipe-separated fields
                        item['synonyms'] = [s.strip() for s in (row.get('synonyms') or '').split('|') if s.strip()]
                        item['substitutions'] = [s.strip() for s in (row.get('substitutions') or '').split('|') if s.strip()]
                        item['categories'] = [s.strip() for s in (row.get('categories') or '').split('|') if s.strip()]
                        item['tags'] = [s.strip() for s in (row.get('tags') or '').split('|') if s.strip()]
                        out['ingredients'].append(item)
            return out
        raise CommandError(f"Unsupported input format: {inferred}")
