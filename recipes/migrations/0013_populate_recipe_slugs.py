from django.db import migrations
from django.utils.text import slugify

def gen_unique_slug(apps, schema_editor):
    Recipe = apps.get_model('recipes', 'Recipe')
    for recipe in Recipe.objects.all():
        base_slug = slugify(recipe.title)
        slug = base_slug
        i = 1
        while Recipe.objects.filter(slug=slug).exclude(pk=recipe.pk).exists() or not slug:
            slug = f"{base_slug}-{i}"
            i += 1
        recipe.slug = slug
        recipe.save()

class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0012_recipe_slug'),
    ]
    operations = [
        migrations.RunPython(gen_unique_slug, reverse_code=migrations.RunPython.noop),
    ]
