from django.core.management.base import BaseCommand
from recipes.models import Recipe

class Command(BaseCommand):
    help = 'Check Recipe model fields'

    def handle(self, *args, **options):
        # Get all field names
        field_names = [f.name for f in Recipe._meta.get_fields()]
        self.stdout.write(f"Recipe model fields: {field_names}")
        
        # Check if counter fields exist
        for field_name in ['views', 'likes', 'comments', 'saves']:
            try:
                field = Recipe._meta.get_field(field_name)
                self.stdout.write(f"Field {field_name} exists: {field}")
            except:
                self.stdout.write(f"Field {field_name} does not exist")
        
        # Check if relation fields exist
        for field_name in ['ratings', 'likes', 'comments']:
            try:
                related_objects = [
                    f for f in Recipe._meta.get_fields() 
                    if (f.is_relation and f.related_model and f.name == field_name)
                ]
                self.stdout.write(f"Relation {field_name}: {related_objects}")
            except:
                self.stdout.write(f"Error checking relation {field_name}")
