from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0025_remove_recipeingredient_unique_recipe_ingredient_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='views',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='recipe',
            name='saves',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='recipe',
            name='likes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='recipe',
            name='comments',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
