document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle (same as index.js)
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    const authButtons = document.querySelector('.auth-buttons');
    
    mobileMenuBtn.addEventListener('click', function() {
        navLinks.classList.toggle('active');
        authButtons.classList.toggle('active');
        this.querySelector('i').classList.toggle('fa-times');
    });

    // Logout Functionality
    const logoutBtn = document.getElementById('logoutBtn');
    logoutBtn.addEventListener('click', function() {
        // In a real app, you would:
        // 1. Send a logout request to your server
        // 2. Clear any client-side authentication tokens
        // 3. Redirect to home page
        
        // For this demo, we'll just redirect
        window.location.href = 'index.html';
    });

    // Load User Data (simulated)
    function loadUserData() {
        // In a real app, this would come from your backend/API
        // For demo, we'll use sessionStorage (or localStorage for persistence)
        const userData = {
            name: 'Alex Johnson',
            stats: {
                mealsPlanned: 7,
                recipesTried: 12,
                healthyMeals: '85%',
                moneySaved: '$45'
            },
            mealPlan: {
                // Sample meal plan data
            },
            recentRecipes: [
                {
                    id: 1,
                    name: 'Mediterranean Salad',
                    image: 'https://images.unsplash.com/photo-1546793665-c74683f339c1',
                    time: '15 mins',
                    rating: 4.5
                },
                // More recipes...
            ]
        };

        // Display user data
        document.getElementById('userName').textContent = userData.name;
        document.getElementById('mealsPlanned').textContent = userData.stats.mealsPlanned;
        document.getElementById('recipesTried').textContent = userData.stats.recipesTried;
        document.getElementById('healthyMeals').textContent = userData.stats.healthyMeals;

        // Populate recent recipes
        const recipesGrid = document.querySelector('.recipes-grid');
        if (recipesGrid && userData.recentRecipes) {
            recipesGrid.innerHTML = userData.recentRecipes.map(recipe => `
                <div class="recipe-card">
                    <div class="recipe-image" style="background-image: url("/images/WhatsApp Image 2025-05-27 at 22.13.58_bc2e87a5"></div>
                    <div class="recipe-info">
                        <h3>${recipe.name}</h3>
                        <p>Scotched Egg with Baked Dough</p>
                        <div class="recipe-meta">
                            <span><i class="fas fa-clock"></i> ${recipe.time}</span>
                            <span><i class="fas fa-star"></i> ${recipe.rating}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }

    // Initialize the dashboard
    loadUserData();
});