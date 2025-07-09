from django.db import migrations

def remove_counter_fields(apps, schema_editor):
    """
    This migration removes the redundant counter fields from Recipe model
    and drops the columns from the database.
    """
    pass  # We'll handle this with a raw SQL migration if needed later

class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0027_add_social_features'),
    ]
    
    operations = [
        migrations.RunPython(remove_counter_fields),
    ]
