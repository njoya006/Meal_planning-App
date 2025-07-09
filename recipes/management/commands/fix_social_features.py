import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Fix migrations and database issues for recipe social features'

    def handle(self, *args, **options):
        # Step 1: Show current migrations
        self.stdout.write(self.style.SUCCESS('Current migrations:'))
        os.system('python manage.py showmigrations recipes')
        
        # Step 2: Backup database
        self.stdout.write(self.style.SUCCESS('\nBacking up database...'))
        os.system('copy db.sqlite3 db.sqlite3.backup')
        
        # Step 3: Delete all problematic migration files
        self.stdout.write(self.style.SUCCESS('\nDeleting problematic migration files...'))
        migration_files = [
            'recipes/migrations/0029_fix_database_schema.py',
            'recipes/migrations/0030_update_related_names.py',
            'recipes/migrations/__pycache__/0029_fix_database_schema.cpython-*.pyc',
            'recipes/migrations/__pycache__/0030_update_related_names.cpython-*.pyc'
        ]
        for file in migration_files:
            try:
                if '*' in file:
                    # For wildcard files, use os.system
                    os.system(f'del {file}')
                else:
                    if os.path.exists(file):
                        os.remove(file)
                        self.stdout.write(f'Deleted {file}')
                    else:
                        self.stdout.write(f'{file} does not exist')
            except Exception as e:
                self.stdout.write(f'Error deleting {file}: {e}')

        # Step 4: Create a fresh migration
        self.stdout.write(self.style.SUCCESS('\nCreating new migration...'))
        os.system('python manage.py makemigrations recipes --name fix_social_features')
        
        # Step 5: Apply the migration
        self.stdout.write(self.style.SUCCESS('\nApplying migration...'))
        os.system('python manage.py migrate')
        
        # Step 6: Show final migration status
        self.stdout.write(self.style.SUCCESS('\nFinal migration status:'))
        os.system('python manage.py showmigrations recipes')
