// JustEat - Main JavaScript Functions

// Toast Notification System
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span>${message}</span>
            <button class="close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Cart Management
class CartManager {
    constructor() {
        this.updateCartCount();
    }
    
    async addToCart(menuItemId, quantity = 1, specialInstructions = '') {
        try {
            const response = await fetch('/customer/add-to-cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    menu_item_id: menuItemId,
                    quantity: quantity,
                    special_instructions: specialInstructions
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast(data.message, 'success');
                this.updateCartCount();
            } else {
                showToast(data.message, 'error');
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            showToast('Failed to add item to cart', 'error');
        }
    }
    
    async updateCartCount() {
        try {
            const response = await fetch('/api/cart/count');
            if (response.ok) {
                const data = await response.json();
                const cartBadge = document.querySelector('.cart-badge');
                if (cartBadge) {
                    cartBadge.textContent = data.count;
                    cartBadge.style.display = data.count > 0 ? 'flex' : 'none';
                }
            }
        } catch (error) {
            console.error('Error updating cart count:', error);
        }
    }
}

// Modal Management
class ModalManager {
    static show(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }
    
    static hide(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }
    
    static hideAll() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
        document.body.style.overflow = 'auto';
    }
}

// Search and Filter Functions
function filterRestaurants() {
    const searchInput = document.getElementById('search-input');
    const cuisineFilter = document.getElementById('cuisine-filter');
    const sortFilter = document.getElementById('sort-filter');
    
    if (searchInput && cuisineFilter && sortFilter) {
        const params = new URLSearchParams();
        
        if (searchInput.value) params.append('search', searchInput.value);
        if (cuisineFilter.value) params.append('cuisine', cuisineFilter.value);
        if (sortFilter.value) params.append('sort', sortFilter.value);
        
        window.location.href = `/customer/restaurants?${params.toString()}`;
    }
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Order Management
async function placeOrder(restaurantId, notes = '') {
    try {
        const response = await fetch('/customer/place-order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                restaurant_id: restaurantId,
                notes: notes
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            setTimeout(() => {
                window.location.href = `/customer/order/${data.order_id}`;
            }, 2000);
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        console.error('Error placing order:', error);
        showToast('Failed to place order', 'error');
    }
}

// Favorite Management
async function toggleFavorite(restaurantId) {
    try {
        const response = await fetch('/api/favorites/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                restaurant_id: restaurantId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const favoriteBtn = document.querySelector(`[data-restaurant-id="${restaurantId}"]`);
            if (favoriteBtn) {
                favoriteBtn.classList.toggle('active');
                favoriteBtn.innerHTML = data.is_favorite ? '❤️' : '🤍';
            }
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
        showToast('Failed to update favorite', 'error');
    }
}

// Form Validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    return isValid;
}

// Loading State Management
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="spinner"></div>';
    }
}

function hideLoading(elementId, originalContent) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = originalContent;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize cart manager
    window.cartManager = new CartManager();
    
    // Setup search debouncing
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterRestaurants, 500));
    }
    
    // Setup filter change handlers
    const cuisineFilter = document.getElementById('cuisine-filter');
    const sortFilter = document.getElementById('sort-filter');
    
    if (cuisineFilter) {
        cuisineFilter.addEventListener('change', filterRestaurants);
    }
    
    if (sortFilter) {
        sortFilter.addEventListener('change', filterRestaurants);
    }
    
    // Setup modal close handlers
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            ModalManager.hideAll();
        }
        
        if (e.target.classList.contains('close')) {
            ModalManager.hideAll();
        }
    });
    
    // Setup add to cart buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-to-cart-btn')) {
            e.preventDefault();
            const menuItemId = e.target.dataset.menuItemId;
            const quantity = e.target.dataset.quantity || 1;
            
            if (menuItemId) {
                window.cartManager.addToCart(parseInt(menuItemId), parseInt(quantity));
            }
        }
    });
    
    // Setup favorite buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('favorite-btn')) {
            e.preventDefault();
            const restaurantId = e.target.dataset.restaurantId;
            
            if (restaurantId) {
                toggleFavorite(parseInt(restaurantId));
            }
        }
    });
    
    // Setup quantity controls
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('quantity-btn')) {
            e.preventDefault();
            const action = e.target.dataset.action;
            const input = e.target.parentElement.querySelector('.quantity-input');
            
            if (input) {
                let value = parseInt(input.value) || 1;
                
                if (action === 'increase') {
                    value++;
                } else if (action === 'decrease' && value > 1) {
                    value--;
                }
                
                input.value = value;
            }
        }
    });
    
    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy to clipboard', 'error');
    });
}

// Profile and Menu Management Functions
function showProfileModal() {
    // Create profile modal if it doesn't exist
    let modal = document.getElementById('profileModal');
    if (!modal) {
        modal = createProfileModal();
        document.body.appendChild(modal);
    }
    ModalManager.show('profileModal');
}

function showManageMenuModal() {
    // Redirect to menu management page
    window.location.href = '/restaurant/menu';
}

function showOrdersModal() {
    // Redirect to orders page
    if (window.location.pathname.includes('/restaurant/')) {
        window.location.href = '/restaurant/orders';
    } else {
        window.location.href = '/customer/orders';
    }
}

function createProfileModal() {
    const modal = document.createElement('div');
    modal.id = 'profileModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>User Profile</h2>
                <span class="close" onclick="ModalManager.hide('profileModal')">&times;</span>
            </div>
            <div class="modal-body">
                <p><strong>Username:</strong> ${window.currentUser?.username || 'N/A'}</p>
                <p><strong>Email:</strong> ${window.currentUser?.email || 'N/A'}</p>
                <p><strong>Role:</strong> ${window.currentUser?.role || 'N/A'}</p>
                <p style="margin-top: 1rem; color: #666;">Profile editing coming soon!</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="ModalManager.hide('profileModal')">Close</button>
            </div>
        </div>
    `;
    return modal;
}

// Location Management
async function requestLocation() {
    if (!navigator.geolocation) {
        showToast('Geolocation is not supported by this browser', 'error');
        return;
    }

    try {
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000
            });
        });

        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        // Reverse geocoding to get address (simplified)
        const address = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;

        const response = await fetch('/api/user/location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                latitude: latitude,
                longitude: longitude,
                address: address
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showToast('Location updated successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        console.error('Error getting location:', error);
        showToast('Failed to get location. Please try again.', 'error');
    }
}

function showLocationModal() {
    let modal = document.getElementById('locationModal');
    if (!modal) {
        modal = createLocationModal();
        document.body.appendChild(modal);
    }
    ModalManager.show('locationModal');
}

function createLocationModal() {
    const modal = document.createElement('div');
    modal.id = 'locationModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Set Your Location</h2>
                <span class="close" onclick="ModalManager.hide('locationModal')">&times;</span>
            </div>
            <div class="modal-body">
                <p>Setting your location helps us show you nearby restaurants and accurate delivery times.</p>
                <div class="location-options">
                    <button class="btn btn-primary" onclick="requestLocation()">
                        <i class="fas fa-location-arrow"></i> Use Current Location
                    </button>
                    <div class="manual-location mt-3">
                        <h4>Or enter manually:</h4>
                        <input type="text" id="manualAddress" class="form-control" placeholder="Enter your address">
                        <button class="btn btn-outline mt-2" onclick="setManualLocation()">Set Location</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    return modal;
}

async function setManualLocation() {
    const address = document.getElementById('manualAddress').value.trim();
    if (!address) {
        showToast('Please enter an address', 'error');
        return;
    }

    // For demo purposes, we'll use a simple geocoding simulation
    // In a real app, you'd use Google Maps Geocoding API or similar
    const mockCoords = {
        latitude: 40.7128 + (Math.random() - 0.5) * 0.1,
        longitude: -74.0060 + (Math.random() - 0.5) * 0.1
    };

    try {
        const response = await fetch('/api/user/location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                latitude: mockCoords.latitude,
                longitude: mockCoords.longitude,
                address: address
            })
        });

        const data = await response.json();
        
        if (data.success) {
            showToast('Location updated successfully!', 'success');
            ModalManager.hide('locationModal');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        console.error('Error setting location:', error);
        showToast('Failed to set location', 'error');
    }
}

// Export functions for global use
window.showToast = showToast;
window.ModalManager = ModalManager;
window.placeOrder = placeOrder;
window.toggleFavorite = toggleFavorite;
window.validateForm = validateForm;
window.formatCurrency = formatCurrency;
window.formatTime = formatTime;
window.showProfileModal = showProfileModal;
window.showManageMenuModal = showManageMenuModal;
window.showOrdersModal = showOrdersModal;
window.requestLocation = requestLocation;
window.showLocationModal = showLocationModal;
window.setManualLocation = setManualLocation;
