from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0013_populate_recipe_slugs'),
    ]
    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, unique=True),
        ),
    ]
