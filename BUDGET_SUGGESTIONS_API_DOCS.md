# 🎯 ChopSmo Budget-Based Recipe Suggestions - API Documentation

## 📋 Overview
The ChopSmo application now supports **budget-based recipe suggestions** alongside the existing ingredient-based suggestions. All costs are in **francs**.

---

## 🚀 Available Endpoints

### 1. **Budget-Based Recipe Suggestions**
- **URL:** `POST /api/recipes/suggest-by-budget/`
- **Description:** Get recipes that fit within a specified budget in francs
- **Authentication:** **Required** - Token authentication
- **Headers:** `Authorization: Token <user_token>`
- **Request Body:**
  ```json
  {
    "budget": 15.00
  }
  ```
- **Response Example:**
  ```json
  {
    "suggested_recipes": [
      {
        "id": 1,
        "title": "Budget Chicken Rice",
        "description": "A simple budget-friendly chicken rice dish",
        "estimated_cost": "10.50",
        "servings": 4,
        "prep_time": 20,
        "cook_time": 30,
        "difficulty": "easy",
        "ingredients": [
          {
            "ingredient": {"id": 1, "name": "Chicken"},
            "quantity": 500,
            "unit": "g"
          }
        ],
        "contributor": {
          "username": "chef_user",
          "is_verified_contributor": true
        },
        "categories": [{"id": 1, "name": "Main Course"}],
        "image": "https://example.com/recipe-image.jpg"
      },
      {
        "id": 3,
        "title": "Garden Salad",
        "description": "Fresh garden salad",
        "estimated_cost": null,
        "servings": 2,
        "prep_time": 10,
        "cook_time": 0,
        "difficulty": "easy",
        "ingredients": [...],
        "contributor": {...}
      }
    ],
    "info": "Recipes under budget 15.0 francs."
  }
  ```

### 2. **Ingredient-Based Recipe Suggestions** (Existing)
- **URL:** `POST /api/recipes/suggest-by-ingredients/`
- **Description:** Get recipes based on available ingredients
- **Authentication:** **Required** - Token authentication
- **Headers:** `Authorization: Token <user_token>`
- **Request Body:**
  ```json
  {
    "ingredient_names": ["chicken", "rice", "tomato", "onion"]
  }
  ```
- **Note:** Minimum 4 ingredients required

### 3. **Search Recipes by Name**
- **URL:** `GET /api/recipes/search/?name=<search_term>`
- **Description:** Search for recipes by name (partial matching, case-insensitive)
- **Authentication:** **Required** - Token authentication
- **Headers:** `Authorization: Token <user_token>`
- **Query Parameters:**
  - `name` (required): The name or partial name to search for
- **Example Request:** `GET /api/recipes/search/?name=chicken`
- **Response Example:**
  ```json
  {
    "count": 2,
    "results": [
      {
        "id": 1,
        "title": "Budget Chicken Rice",
        "description": "A simple budget-friendly chicken rice dish",
        "estimated_cost": "10.50",
        "servings": 4,
        "prep_time": 20,
        "cook_time": 30,
        "difficulty": "easy",
        "contributor": {
          "username": "chef_user",
          "is_verified_contributor": true
        }
      },
      {
        "id": 7,
        "title": "Chicken Curry",
        "description": "Spicy chicken curry",
        "estimated_cost": "18.00",
        "servings": 6,
        "prep_time": 15,
        "cook_time": 45,
        "difficulty": "medium",
        "contributor": {...}
      }
    ],
    "message": "Found 2 recipe(s) matching \"chicken\""
  }
  ```

### 4. **Get Recipe by Exact Name**
- **URL:** `GET /api/recipes/by-name/<recipe-name>/`
- **Description:** Get a specific recipe by its exact name (case-insensitive)
- **Authentication:** **Required** - Token authentication
- **Headers:** `Authorization: Token <user_token>`
- **URL Format:** Replace spaces with hyphens in the recipe name
- **Example Request:** `GET /api/recipes/by-name/chicken-curry/`
- **Response Example:**
  ```json
  {
    "id": 7,
    "title": "Chicken Curry",
    "description": "Spicy chicken curry with aromatic spices",
    "instructions": "1. Heat oil in pan...",
    "estimated_cost": "18.00",
    "servings": 6,
    "prep_time": 15,
    "cook_time": 45,
    "difficulty": "medium",
    "ingredients": [
      {
        "ingredient": {"id": 1, "name": "Chicken"},
        "quantity": 800,
        "unit": "g",
        "preparation": "cut into pieces"
      }
    ],
    "contributor": {
      "username": "spice_master",
      "is_verified_contributor": true
    },
    "categories": [{"id": 1, "name": "Main Course"}],
    "image": "https://example.com/chicken-curry.jpg"
  }
  ```

### 5. **Create Recipe with Optional Cost**
- **URL:** `POST /api/recipes/`
- **Description:** Create a new recipe with optional estimated cost
- **Authentication:** Required (verified contributors only)
- **Headers:** `Authorization: Token <user_token>`
- **Request Body:**
  ```json
  {
    "title": "My Amazing Recipe",
    "description": "Delicious homemade dish",
    "instructions": "Step by step cooking instructions",
    "estimated_cost": 12.50,  // OPTIONAL - cost in francs
    "servings": 4,
    "prep_time": 15,
    "cook_time": 30,
    "difficulty": "easy",
    "ingredients_data": [
      {
        "ingredient_name": "Chicken",
        "quantity": 500,
        "unit": "g",
        "preparation": "diced"
      },
      {
        "ingredient_name": "Rice",
        "quantity": 200,
        "unit": "g"
      }
    ],
    "category_names": ["Main Course"],
    "cuisine_names": ["French"],
    "tag_names": ["Easy", "Quick"]
  }
  ```

### 6. **Get All Recipes**
- **URL:** `GET /api/recipes/`
- **Description:** Get all active recipes (includes estimated_cost field)
- **Authentication:** **Required** - Token authentication
- **Headers:** `Authorization: Token <user_token>`

### 7. **Update Recipe**
- **URL:** `PUT /api/recipes/{id}/` or `PATCH /api/recipes/{id}/`
- **Description:** Update existing recipe (can add/modify estimated_cost)
- **Authentication:** Required (recipe owner or admin)

---

## 💰 Currency Information
- **All costs are in francs**
- The `estimated_cost` field accepts decimal values (e.g., 12.50)
- Recipes without cost data (`estimated_cost: null`) are included in budget searches
- Maximum cost precision: 8 digits with 2 decimal places

---

## 🎨 Frontend Implementation Examples

### JavaScript/React Example:

```javascript
// Budget-based suggestions with authentication
const getBudgetSuggestions = async (budget, userToken) => {
  try {
    const response = await fetch('/api/recipes/suggest-by-budget/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${userToken}`  // Required authentication
      },
      body: JSON.stringify({ budget: parseFloat(budget) })
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication required. Please log in.');
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Display recipes with franc pricing
    data.suggested_recipes.forEach(recipe => {
      const cost = recipe.estimated_cost 
        ? `${recipe.estimated_cost} francs` 
        : 'Cost not specified';
      console.log(`${recipe.title}: ${cost}`);
    });
    
    return data;
  } catch (error) {
    console.error('Error fetching budget suggestions:', error);
    throw error;
  }
};

// Ingredient-based suggestions with authentication
const getIngredientSuggestions = async (ingredients, userToken) => {
  try {
    const response = await fetch('/api/recipes/suggest-by-ingredients/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${userToken}`  // Required authentication
      },
      body: JSON.stringify({ ingredient_names: ingredients })
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication required. Please log in.');
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching ingredient suggestions:', error);
    throw error;
  }
};

// Create recipe with optional cost
const createRecipe = async (recipeData, userToken) => {
  const payload = {
    title: recipeData.title,
    description: recipeData.description,
    instructions: recipeData.instructions,
    servings: recipeData.servings,
    prep_time: recipeData.prepTime,
    cook_time: recipeData.cookTime,
    difficulty: recipeData.difficulty,
    ingredients_data: recipeData.ingredients,
    category_names: recipeData.categories,
    // Only include estimated_cost if provided
    ...(recipeData.estimatedCost && { 
      estimated_cost: parseFloat(recipeData.estimatedCost) 
    })
  };
  
  try {
    const response = await fetch('/api/recipes/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${userToken}`
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create recipe');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error creating recipe:', error);
    throw error;
  }
};

// Usage examples
async function examples() {
  const userToken = 'your_user_token_here';  // Get from login response
  
  // Get recipes under 20 francs (requires authentication)
  const budgetRecipes = await getBudgetSuggestions(20, userToken);
  
  // Get ingredient-based suggestions (requires authentication)
  const ingredientRecipes = await getIngredientSuggestions(['chicken', 'rice', 'tomato', 'onion'], userToken);
  
  // Create a new recipe with cost (requires authentication)
  const newRecipe = await createRecipe({
    title: "French Onion Soup",
    description: "Classic French soup",
    instructions: "Caramelize onions...",
    estimatedCost: 8.75, // Optional
    servings: 4,
    prepTime: 15,
    cookTime: 45,
    difficulty: "medium",
    ingredients: [
      {
        ingredient_name: "Onions",
        quantity: 4,
        unit: "piece"
      },
      {
        ingredient_name: "Beef Broth",
        quantity: 1,
        unit: "l"
      }
    ],
    categories: ["Soup"]
  }, userToken);
}
```

---

## ✅ Key Features

1. **✅ Authentication Required:** All recipe suggestion endpoints require user authentication
2. **✅ Backward Compatibility:** Existing functionality unchanged
3. **✅ Optional Cost Field:** Recipes can be created without estimated_cost
4. **✅ Smart Budget Logic:** Includes recipes with missing cost data
5. **✅ Franc Currency:** All monetary values in francs
6. **✅ Robust Error Handling:** Proper validation and error messages
7. **✅ Dual Suggestion System:** Both budget-based and ingredient-based suggestions
8. **✅ Secure Access:** Token-based authentication for all endpoints

---

## 🚨 Important Notes

- **Authentication is required** for all recipe suggestion endpoints
- Users must provide a valid authentication token in the `Authorization` header
- The `estimated_cost` field is **completely optional**
- Recipes without cost data are **included** in budget suggestions
- Budget filtering does **not affect** ingredient-based suggestions
- All existing recipe creation/editing functionality remains **unchanged**
- Users can create recipes exactly as before without specifying cost
- 401 Unauthorized will be returned if authentication token is missing or invalid

---

## 🧪 Testing

The backend has been tested with various scenarios:
- Recipes within budget ✅
- Recipes over budget (excluded) ✅
- Recipes with no cost data (included) ✅
- Invalid budget values (error handling) ✅
- Existing ingredient suggestions (unaffected) ✅

Your frontend can immediately start using these endpoints!
