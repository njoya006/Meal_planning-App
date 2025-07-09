from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0028_fix_counter_fields'),
    ]

    operations = [
        migrations.RunSQL(
            # This is a SQL operations migration that creates the tables directly
            # We've fixed the related_names in the models, now we need to make sure the tables exist
            sql="""
            -- Create RecipeLike table if it doesn't exist
            CREATE TABLE IF NOT EXISTS "recipes_recipelike" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "created_at" datetime NOT NULL,
                "recipe_id" integer NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" integer NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            
            -- Create RecipeComment table if it doesn't exist
            CREATE TABLE IF NOT EXISTS "recipes_recipecomment" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "content" text NOT NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "is_approved" bool NOT NULL,
                "recipe_id" integer NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" integer NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            
            -- Create RecipeRating table if it doesn't exist
            CREATE TABLE IF NOT EXISTS "recipes_reciperating" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "rating" smallint unsigned NOT NULL CHECK ("rating" >= 0),
                "review" text NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "recipe_id" integer NOT NULL REFERENCES "recipes_recipe" ("id") DEFERRABLE INITIALLY DEFERRED,
                "user_id" integer NOT NULL REFERENCES "users_customuser" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            
            -- Create unique constraints
            CREATE UNIQUE INDEX IF NOT EXISTS "recipes_recipelike_recipe_id_user_id" ON "recipes_recipelike" ("recipe_id", "user_id");
            CREATE UNIQUE INDEX IF NOT EXISTS "recipes_reciperating_recipe_id_user_id" ON "recipes_reciperating" ("recipe_id", "user_id");
            
            -- Create indices
            CREATE INDEX IF NOT EXISTS "recipes_recipecomment_recipe_id" ON "recipes_recipecomment" ("recipe_id");
            CREATE INDEX IF NOT EXISTS "recipes_recipecomment_user_id" ON "recipes_recipecomment" ("user_id");
            CREATE INDEX IF NOT EXISTS "recipes_recipelike_recipe_id" ON "recipes_recipelike" ("recipe_id");
            CREATE INDEX IF NOT EXISTS "recipes_recipelike_user_id" ON "recipes_recipelike" ("user_id");
            CREATE INDEX IF NOT EXISTS "recipes_reciperating_recipe_id" ON "recipes_reciperating" ("recipe_id");
            CREATE INDEX IF NOT EXISTS "recipes_reciperating_user_id" ON "recipes_reciperating" ("user_id");
            """,
            reverse_sql=""" 
            -- Drop tables in reverse
            DROP TABLE IF EXISTS "recipes_reciperating";
            DROP TABLE IF EXISTS "recipes_recipecomment";
            DROP TABLE IF EXISTS "recipes_recipelike";
            """
        ),
    ]
