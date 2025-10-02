from django.db import migrations


def create_social_tables(apps, schema_editor):
    vendor = schema_editor.connection.vendor

    if vendor == 'postgresql':
        statements = [
            '''CREATE TABLE IF NOT EXISTS "recipes_recipelike" (
                "id" BIGSERIAL PRIMARY KEY,
                "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                "recipe_id" INTEGER NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" INTEGER NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );''',
            '''CREATE TABLE IF NOT EXISTS "recipes_recipecomment" (
                "id" BIGSERIAL PRIMARY KEY,
                "content" TEXT NOT NULL,
                "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                "is_approved" BOOLEAN NOT NULL,
                "recipe_id" INTEGER NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" INTEGER NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );''',
            '''CREATE TABLE IF NOT EXISTS "recipes_reciperating" (
                "id" BIGSERIAL PRIMARY KEY,
                "rating" SMALLINT NOT NULL CHECK ("rating" >= 0),
                "review" TEXT NULL,
                "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                "recipe_id" INTEGER NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" INTEGER NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );''',
            'CREATE UNIQUE INDEX IF NOT EXISTS "recipes_recipelike_recipe_id_user_id" ON "recipes_recipelike" ("recipe_id", "user_id");',
            'CREATE UNIQUE INDEX IF NOT EXISTS "recipes_reciperating_recipe_id_user_id" ON "recipes_reciperating" ("recipe_id", "user_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_recipecomment_recipe_id" ON "recipes_recipecomment" ("recipe_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_recipecomment_user_id" ON "recipes_recipecomment" ("user_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_recipelike_recipe_id" ON "recipes_recipelike" ("recipe_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_recipelike_user_id" ON "recipes_recipelike" ("user_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_reciperating_recipe_id" ON "recipes_reciperating" ("recipe_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_reciperating_user_id" ON "recipes_reciperating" ("user_id");',
        ]
    else:
        statements = [
            '''CREATE TABLE IF NOT EXISTS "recipes_recipelike" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "created_at" datetime NOT NULL,
                "recipe_id" integer NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" integer NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );''',
            '''CREATE TABLE IF NOT EXISTS "recipes_recipecomment" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "content" text NOT NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "is_approved" bool NOT NULL,
                "recipe_id" integer NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" integer NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );''',
            '''CREATE TABLE IF NOT EXISTS "recipes_reciperating" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "rating" smallint NOT NULL CHECK ("rating" >= 0),
                "review" text NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "recipe_id" integer NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" integer NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );''',
            'CREATE UNIQUE INDEX IF NOT EXISTS "recipes_recipelike_recipe_id_user_id" ON "recipes_recipelike" ("recipe_id", "user_id");',
            'CREATE UNIQUE INDEX IF NOT EXISTS "recipes_reciperating_recipe_id_user_id" ON "recipes_reciperating" ("recipe_id", "user_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_recipecomment_recipe_id" ON "recipes_recipecomment" ("recipe_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_recipecomment_user_id" ON "recipes_recipecomment" ("user_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_recipelike_recipe_id" ON "recipes_recipelike" ("recipe_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_recipelike_user_id" ON "recipes_recipelike" ("user_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_reciperating_recipe_id" ON "recipes_reciperating" ("recipe_id");',
            'CREATE INDEX IF NOT EXISTS "recipes_reciperating_user_id" ON "recipes_reciperating" ("user_id");',
        ]

    for statement in statements:
        schema_editor.execute(statement)


def drop_social_tables(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    cascade_suffix = ' CASCADE' if vendor == 'postgresql' else ''

    statements = [
        f'DROP TABLE IF EXISTS "recipes_reciperating"{cascade_suffix};',
        f'DROP TABLE IF EXISTS "recipes_recipecomment"{cascade_suffix};',
        f'DROP TABLE IF EXISTS "recipes_recipelike"{cascade_suffix};',
    ]

    for statement in statements:
        schema_editor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0028_fix_counter_fields'),
    ]

    operations = [
        migrations.RunPython(create_social_tables, drop_social_tables),
    ]
