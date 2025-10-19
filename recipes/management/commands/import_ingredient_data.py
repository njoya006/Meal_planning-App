"""Import ingredient default weights and prices from CSV.

CSV format: name,default_unit_weight_g,price_per_kg
Example:
egg,50,1200
plantain,200,400
rice,1000,800

Options:
  --dry-run: show changes without applying
  --yes: apply changes without prompt
"""
from django.core.management.base import BaseCommand, CommandError
import csv
from decimal import Decimal, InvalidOperation
from recipes.models import Ingredient, IngredientPrice
from django.db import transaction
import os

class Command(BaseCommand):
    help = 'Import ingredient default weights (grams) and price_per_kg from CSV.'

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str, help='Path to CSV file')
        parser.add_argument('--dry-run', action='store_true', dest='dry_run', help='Show changes without applying')
        parser.add_argument('--yes', action='store_true', dest='yes', help='Apply changes without prompt')

    def handle(self, *args, **options):
        path = options['csvfile']
        dry_run = options['dry_run']
        auto_yes = options['yes']

        if not os.path.exists(path):
            raise CommandError(f'File not found: {path}')

        changes = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=['name', 'default_unit_weight_g', 'price_per_kg'])
            for i, row in enumerate(reader, start=1):
                name = (row.get('name') or '').strip()
                if not name:
                    self.stdout.write(self.style.WARNING(f'Row {i}: empty name, skipping'))
                    continue
                weight = None
                price = None
                w_raw = (row.get('default_unit_weight_g') or '').strip()
                p_raw = (row.get('price_per_kg') or '').strip()
                if w_raw:
                    try:
                        weight = float(w_raw)
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f'Row {i}: invalid weight "{w_raw}" for {name}, skipping weight'))
                if p_raw:
                    try:
                        price = Decimal(p_raw)
                    except InvalidOperation:
                        self.stdout.write(self.style.WARNING(f'Row {i}: invalid price "{p_raw}" for {name}, skipping price'))

                changes.append({'name': name, 'weight': weight, 'price': price})

        if not changes:
            self.stdout.write('No valid rows found in CSV.')
            return

        # Show summary
        self.stdout.write(self.style.MIGRATE_HEADING('Planned changes:'))
        for c in changes:
            self.stdout.write(f"- {c['name']}: weight={c['weight']} g, price_per_kg={c['price']}")

        if dry_run:
            self.stdout.write(self.style.NOTICE('Dry run mode - no changes applied.'))
            return

        if not auto_yes:
            confirm = input('Apply changes? [y/N]: ').strip().lower()
            if confirm != 'y':
                self.stdout.write('Aborted by user.')
                return

        applied = 0
        with transaction.atomic():
            for c in changes:
                name = c['name']
                weight = c['weight']
                price = c['price']
                ing, created = Ingredient.objects.get_or_create(name=name.title())
                updated = False
                if weight is not None and ing.default_unit_weight_g != weight:
                    ing.default_unit_weight_g = weight
                    ing.save()
                    updated = True
                # Upsert IngredientPrice
                if price is not None:
                    ip, ip_created = IngredientPrice.objects.get_or_create(ingredient=ing, defaults={'price_per_kg': price})
                    if not ip_created and ip.price_per_kg != price:
                        ip.price_per_kg = price
                        ip.save()
                        updated = True
                if created:
                    applied += 1
                elif updated:
                    applied += 1

        self.stdout.write(self.style.SUCCESS(f'Applied changes for {applied} ingredients.'))
