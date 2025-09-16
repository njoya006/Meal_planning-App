import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
import django
django.setup()
from django.test.runner import DiscoverRunner

runner = DiscoverRunner(verbosity=2, interactive=False)
failures = runner.run_tests(['billing'])
if failures:
    print('\nTESTS FAILED:', failures)
    sys.exit(1)
print('\nALL TESTS OK')
