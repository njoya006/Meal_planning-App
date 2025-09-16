from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0032_recipe_estimated_cost'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='recipes/images/')),
                ('caption', models.CharField(blank=True, max_length=255)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_recipe_images', to='users.customuser')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='recipes.recipe')),
            ],
            options={'ordering': ['order', 'id']},
        ),
        migrations.CreateModel(
            name='InstructionStepImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step_index', models.PositiveIntegerField()),
                ('image', models.ImageField(upload_to='recipes/steps/')),
                ('caption', models.CharField(blank=True, max_length=255)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_step_images', to='users.customuser')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='step_images', to='recipes.recipe')),
            ],
            options={'ordering': ['step_index'], 'unique_together': {('recipe', 'step_index')}},
        ),
    ]
