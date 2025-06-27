document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle (reuse from your existing JS)
    
    // FAQ Accordion Functionality
    const faqQuestions = document.querySelectorAll('.faq-question');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', () => {
            const faqItem = question.parentElement;
            const isActive = faqItem.classList.contains('active');
            
            // Close all other items
            document.querySelectorAll('.faq-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Toggle current item
            if (!isActive) {
                faqItem.classList.add('active');
            }
        });
    });

    // FAQ Category Filtering
    const categories = document.querySelectorAll('.category');
    
    categories.forEach(category => {
        category.addEventListener('click', () => {
            // Update active category
            categories.forEach(c => c.classList.remove('active'));
            category.classList.add('active');
            
            // Filter FAQs
            const categoryName = category.dataset.category;
            const allCategories = document.querySelectorAll('.faq-category');
            
            allCategories.forEach(faqCategory => {
                if (categoryName === 'all' || faqCategory.dataset.category === categoryName) {
                    faqCategory.style.display = 'block';
                } else {
                    faqCategory.style.display = 'none';
                }
            });
        });
    });

    // FAQ Search Functionality
    const faqSearch = document.getElementById('faqSearch');
    const searchButton = document.querySelector('.search-faq button');
    
    function searchFAQs() {
        const searchTerm = faqSearch.value.toLowerCase();
        const faqItems = document.querySelectorAll('.faq-item');
        
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question').textContent.toLowerCase();
            const answer = item.querySelector('.faq-answer').textContent.toLowerCase();
            
            if (question.includes(searchTerm) || answer.includes(searchTerm)) {
                item.style.display = 'block';
                if (searchTerm && !item.classList.contains('active')) {
                    item.classList.add('active');
                }
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    faqSearch.addEventListener('keyup', searchFAQs);
    searchButton.addEventListener('click', searchFAQs);
});