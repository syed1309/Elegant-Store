// Slider functionality
function slideLeft(section) {
    const slider = document.getElementById(`${section}-slider`);
    if (!slider) return;
    
    const cardWidth = 280 + 20; // card width + gap
    slider.scrollLeft -= cardWidth * 2; // Scroll 2 cards at a time
    updateArrowVisibility(section);
}

function slideRight(section) {
    const slider = document.getElementById(`${section}-slider`);
    if (!slider) return;
    
    const cardWidth = 280 + 20; // card width + gap
    slider.scrollLeft += cardWidth * 2; // Scroll 2 cards at a time
    updateArrowVisibility(section);
}

function updateArrowVisibility(section) {
    const slider = document.getElementById(`${section}-slider`);
    if (!slider) return;
    
    const prevBtn = slider.previousElementSibling;
    const nextBtn = slider.nextElementSibling;
    
    if (!prevBtn || !nextBtn) return;
    
    // Show/hide prev button
    if (slider.scrollLeft <= 10) {
        prevBtn.style.opacity = '0.3';
        prevBtn.style.cursor = 'not-allowed';
    } else {
        prevBtn.style.opacity = '1';
        prevBtn.style.cursor = 'pointer';
    }
    
    // Show/hide next button
    if (slider.scrollLeft >= slider.scrollWidth - slider.clientWidth - 10) {
        nextBtn.style.opacity = '0.3';
        nextBtn.style.cursor = 'not-allowed';
    } else {
        nextBtn.style.opacity = '1';
        nextBtn.style.cursor = 'pointer';
    }
}

// Cart functionality
function addToCart(itemId) {
    fetch(`/cart/add/${itemId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                updateCartCount();
            } else {
                showNotification(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error adding to cart', 'error');
        });
}

// Wishlist functionality
function addToWishlist(itemId, button) {
    fetch(`/wishlist/add/${itemId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                // Update button state visually
                if (button) {
                    button.classList.add('active');
                    button.style.background = '#e74c3c';
                    button.style.color = 'white';
                }
            } else {
                showNotification(data.message, 'info');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error adding to wishlist', 'error');
        });
}

// Login alert
function showLoginAlert() {
    showNotification('Please login to add items to cart or wishlist', 'warning');
}

// Notification system
function showNotification(message, type) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        if (notification.parentNode) {
            document.body.removeChild(notification);
        }
    });

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Different colors for different message types
    let backgroundColor;
    switch(type) {
        case 'success':
            backgroundColor = '#27ae60'; // Green
            break;
        case 'error':
            backgroundColor = '#e74c3c'; // Red
            break;
        case 'info':
            backgroundColor = '#3498db'; // Blue
            break;
        case 'warning':
            backgroundColor = '#f39c12'; // Orange
            break;
        default:
            backgroundColor = '#3498db'; // Blue
    }
    
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${backgroundColor};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Update cart count
function updateCartCount() {
    // Reload the page to get updated cart count
    setTimeout(() => {
        window.location.reload();
    }, 1000);
}

// Mobile menu functionality
function initMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuBtn && navMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            mobileMenuBtn.classList.toggle('active');
        });
    }
}

// Search functionality
function initSearch() {
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="q"]');
            if (searchInput && searchInput.value.trim() === '') {
                e.preventDefault();
                showNotification('Please enter a search term', 'warning');
            }
        });
    }
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize arrow visibility for all sections
    const sections = ['popular', 'new', 'deals'];
    sections.forEach(section => {
        updateArrowVisibility(section);
    });
    
    // Initialize mobile menu
    initMobileMenu();
    
    // Initialize search
    initSearch();
    
    // Add CSS for notifications if not already added
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            .notification {
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: 500;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Add touch/swipe support for mobile sliders
    initTouchSliders();
});

// Touch/swipe support for mobile
function initTouchSliders() {
    const sliders = document.querySelectorAll('.products-slider');
    
    sliders.forEach(slider => {
        let startX;
        let scrollLeft;
        
        slider.addEventListener('touchstart', (e) => {
            startX = e.touches[0].pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
        });
        
        slider.addEventListener('touchmove', (e) => {
            if (!startX) return;
            const x = e.touches[0].pageX - slider.offsetLeft;
            const walk = (x - startX) * 2; // Scroll-fast
            slider.scrollLeft = scrollLeft - walk;
        });
        
        slider.addEventListener('touchend', () => {
            startX = null;
            // Update arrow visibility after touch
            const section = slider.id.replace('-slider', '');
            updateArrowVisibility(section);
        });
    });
}

// Keyboard navigation for sliders
document.addEventListener('keydown', function(e) {
    const activeElement = document.activeElement;
    const slider = activeElement.closest('.products-slider');
    
    if (slider) {
        const section = slider.id.replace('-slider', '');
        const cardWidth = 280 + 20;
        
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            slider.scrollLeft -= cardWidth;
            updateArrowVisibility(section);
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            slider.scrollLeft += cardWidth;
            updateArrowVisibility(section);
        }
    }
});

// Auto-hide arrows on resize
window.addEventListener('resize', function() {
    const sections = ['popular', 'new', 'deals'];
    sections.forEach(section => {
        updateArrowVisibility(section);
    });
});

// Export functions for global access (if needed)
window.HomeJS = {
    slideLeft,
    slideRight,
    addToCart,
    addToWishlist,
    showNotification,
    updateCartCount
};