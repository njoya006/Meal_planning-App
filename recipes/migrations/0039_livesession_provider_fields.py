from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0038_ingredient_default_unit_weight_g'),
    ]

    operations = [
        migrations.AddField(
            model_name='livesession',
            name='external_room_data',
            field=models.JSONField(blank=True, default=dict, help_text='Raw provisioning payload returned by the streaming provider.'),
        ),
        migrations.AddField(
            model_name='livesession',
            name='external_room_name',
            field=models.CharField(blank=True, help_text='Identifier for the external streaming room (e.g., Daily room name).', max_length=255),
        ),
        migrations.AddField(
            model_name='livesession',
            name='external_room_url',
            field=models.URLField(blank=True, help_text='Join URL provided by the external streaming provider.'),
        ),
        migrations.AddField(
            model_name='livesession',
            name='provider',
            field=models.CharField(choices=[('local', 'Local'), ('daily', 'Daily')], default='local', help_text='Streaming backend powering this live session.', max_length=32),
        ),
    ]
