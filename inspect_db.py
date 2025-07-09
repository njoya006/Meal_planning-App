import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check Recipe table structure
cursor.execute('PRAGMA table_info(recipes_recipe)')
recipe_fields = cursor.fetchall()
print("Recipe Table Fields:")
for field in recipe_fields:
    print(field)

# Check if the new tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='recipes_recipelike' OR name='recipes_recipecomment' OR name='recipes_reciperating')")
tables = cursor.fetchall()
print("\nRelated Tables:")
for table in tables:
    print(table[0])

# Check schema of the related tables if they exist
for table in ['recipes_recipelike', 'recipes_recipecomment', 'recipes_reciperating']:
    print(f"\n{table} Fields:")
    cursor.execute(f'PRAGMA table_info({table})')
    fields = cursor.fetchall()
    if fields:
        for field in fields:
            print(field)
    else:
        print("Table doesn't exist")

conn.close()
