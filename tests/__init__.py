"""Top-level tests package to satisfy Django discovery.

This proxy module re-exports the recipe app tests so that running
`manage.py test` without labels works without import errors.
"""

from recipes.tests_suite import *  # noqa: F401,F403
