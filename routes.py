from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import or_, func, desc
from models import db, User, Restaurant, MenuItem, Order, Review, Favorite, Cart, OrderItem
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# -----------------------------
# Helpers
# -----------------------------
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# -----------------------------
# Customer + Auth Routes
# -----------------------------
def register_routes(app):

    # Index
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'customer':
                return redirect(url_for('customer_dashboard'))
            else:
                return redirect(url_for('restaurant_dashboard'))
        return render_template('index.html')

    # Login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            try:
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')

                user = User.query.filter_by(username=username).first()
                if user and check_password_hash(user.password_hash, password):
                    login_user(user, remember=True)
                    flash('Login successful!', 'success')
                    if user.role == 'customer':
                        return redirect(url_for('customer_dashboard'))
                    else:
                        return redirect(url_for('restaurant_dashboard'))
                else:
                    flash('Invalid username or password', 'error')
            except Exception as e:
                logger.error(f'Login error: {str(e)}')
                flash('An error occurred during login', 'error')

        return render_template('login.html')

    # Logout
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out', 'info')
        return redirect(url_for('index'))

    # Signup
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            try:
                username = request.form['username']
                email = request.form['email']
                password = request.form['password']
                confirm_password = request.form['confirm_password']
                role = request.form.get('role', 'customer')

                if not username or not email or not password:
                    flash('All fields are required', 'error')
                    return render_template('signup.html')
                if password != confirm_password:
                    flash('Passwords do not match', 'error')
                    return render_template('signup.html')

                if User.query.filter_by(username=username).first():
                    flash('Username already exists', 'error')
                    return render_template('signup.html')
                if User.query.filter_by(email=email).first():
                    flash('Email already registered', 'error')
                    return render_template('signup.html')

                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password),
                    role=role
                )

                if role == 'customer':
                    user.phone = request.form.get('phone', '')
                    user.address = request.form.get('address', '')
                    user.dietary_restrictions = request.form.get('dietary_restrictions', '')

                db.session.add(user)
                db.session.commit()

                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                logger.error(f'Signup error: {str(e)}')
                flash('An error occurred during registration', 'error')

        return render_template('signup.html')

    # Customer Dashboard
    @app.route('/customer/dashboard')
    @login_required
    @role_required('customer')
    def customer_dashboard():
        restaurants = Restaurant.query.filter_by(is_active=True).all()
        
        # Get favorites - these should be Restaurant objects
        favorites = []
        if hasattr(current_user, 'favorites'):
            favorites = [fav.restaurant for fav in current_user.favorites]
        
        recent_orders = Order.query.filter_by(
            customer_id=current_user.id
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        recommendations = get_recommendations(current_user.id)
        
        return render_template('customer/dashboard.html',
                               restaurants=restaurants,
                               favorites=favorites,
                               recent_orders=recent_orders,
                               recommendations=recommendations)

    # Browse Restaurants
    @app.route('/customer/restaurants')
    @login_required
    @role_required('customer')
    def browse_restaurants():
        search = request.args.get('search', '')
        cuisine = request.args.get('cuisine', '')

        query = Restaurant.query.filter_by(is_active=True)
        if search:
            query = query.filter(or_(
                Restaurant.name.contains(search),
                Restaurant.cuisine_type.contains(search),
                Restaurant.address.contains(search)
            ))
        if cuisine:
            query = query.filter_by(cuisine_type=cuisine)

        restaurants = query.all()
        # Ensure every restaurant has a usable .distance value
        for r in restaurants:
            if getattr(r, "distance", None) is None:
                r.distance = "inf"   # set it to a string instead of float('inf')

        cuisines = [c[0] for c in db.session.query(Restaurant.cuisine_type).distinct()]
        return render_template('customer/restaurants.html',
                               restaurants=restaurants,
                               cuisines=cuisines,
                               current_search=search,
                               current_cuisine=cuisine)

    # Restaurant Menu
    @app.route('/customer/restaurant/<int:restaurant_id>')
    @login_required
    @role_required('customer')
    def restaurant_menu(restaurant_id):
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        menu_items = MenuItem.query.filter_by(
            restaurant_id=restaurant_id, is_available=True
        ).all()

        categories = {}
        for item in menu_items:
            categories.setdefault(item.category, []).append(item)

        is_favorite = Favorite.query.filter_by(
            customer_id=current_user.id, restaurant_id=restaurant_id
        ).first() is not None

        reviews = Review.query.filter_by(
            restaurant_id=restaurant_id
        ).order_by(Review.created_at.desc()).limit(10).all()

        return render_template('customer/restaurant_menu.html',
                               restaurant=restaurant,
                               categories=categories,
                               is_favorite=is_favorite,
                               reviews=reviews)

    # Add to Cart
    @app.route('/customer/cart/add', methods=['POST'])
    @login_required
    @role_required('customer')
    def add_to_cart():
        try:
            menu_item_id = request.form.get('menu_item_id')
            quantity = int(request.form.get('quantity', 1))
            
            menu_item = MenuItem.query.get_or_404(menu_item_id)
            
            cart_item = Cart.query.filter_by(
                customer_id=current_user.id,
                menu_item_id=menu_item_id
            ).first()
            
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = Cart(
                    customer_id=current_user.id,
                    menu_item_id=menu_item_id,
                    quantity=quantity
                )
                db.session.add(cart_item)
            
            db.session.commit()
            flash(f'{menu_item.name} added to cart!', 'success')
            
        except Exception as e:
            logger.error(f'Add to cart error: {str(e)}')
            flash('Error adding item to cart', 'error')
            
        return redirect(request.referrer or url_for('customer_dashboard'))

    # View Cart
    @app.route('/customer/cart')
    @login_required
    @role_required('customer')
    def view_cart():
        cart_items = Cart.query.filter_by(customer_id=current_user.id).all()
        total_price = sum(item.menu_item.price * item.quantity for item in cart_items)
        return render_template('customer/cart.html', 
                               cart_items=cart_items, 
                               total_price=total_price)

    # Update Cart
    @app.route('/customer/cart/update', methods=['POST'])
    @login_required
    @role_required('customer')
    def update_cart():
        try:
            cart_item_id = request.form.get('cart_item_id')
            quantity = int(request.form.get('quantity'))
            
            cart_item = Cart.query.get_or_404(cart_item_id)
            
            if cart_item.customer_id != current_user.id:
                flash('Unauthorized action', 'error')
                return redirect(url_for('view_cart'))
            
            if quantity <= 0:
                db.session.delete(cart_item)
                flash('Item removed from cart', 'info')
            else:
                cart_item.quantity = quantity
                flash('Cart updated', 'success')
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f'Update cart error: {str(e)}')
            flash('Error updating cart', 'error')
            
        return redirect(url_for('view_cart'))

    # Remove from Cart
    @app.route('/customer/cart/remove/<int:cart_item_id>')
    @login_required
    @role_required('customer')
    def remove_from_cart(cart_item_id):
        try:
            cart_item = Cart.query.get_or_404(cart_item_id)
            
            if cart_item.customer_id != current_user.id:
                flash('Unauthorized action', 'error')
                return redirect(url_for('view_cart'))
            
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart', 'info')
            
        except Exception as e:
            logger.error(f'Remove from cart error: {str(e)}')
            flash('Error removing item from cart', 'error')
            
        return redirect(url_for('view_cart'))

    # Checkout
    @app.route('/customer/checkout', methods=['GET', 'POST'])
    @login_required
    @role_required('customer')
    def checkout():
        cart_items = Cart.query.filter_by(customer_id=current_user.id).all()
        
        if not cart_items:
            flash('Your cart is empty', 'error')
            return redirect(url_for('view_cart'))
        
        if request.method == 'POST':
            try:
                delivery_address = request.form.get('delivery_address')
                special_instructions = request.form.get('special_instructions', '')
                
                # Group cart items by restaurant
                restaurants = {}
                for item in cart_items:
                    restaurant_id = item.menu_item.restaurant_id
                    if restaurant_id not in restaurants:
                        restaurants[restaurant_id] = []
                    restaurants[restaurant_id].append(item)
                
                # Create separate orders for each restaurant
                for restaurant_id, items in restaurants.items():
                    total_amount = sum(item.menu_item.price * item.quantity for item in items)
                    
                    order = Order(
                        customer_id=current_user.id,
                        restaurant_id=restaurant_id,
                        total_amount=total_amount,
                        delivery_address=delivery_address,
                        special_instructions=special_instructions,
                        status='pending'
                    )
                    db.session.add(order)
                    db.session.flush()  # To get the order ID
                    
                    # Add order items
                    for item in items:
                        order_item = OrderItem(
                            order_id=order.id,
                            menu_item_id=item.menu_item_id,
                            quantity=item.quantity,
                            price=item.menu_item.price
                        )
                        db.session.add(order_item)
                    
                    # Remove items from cart
                    for item in items:
                        db.session.delete(item)
                
                db.session.commit()
                flash('Orders placed successfully!', 'success')
                return redirect(url_for('order_history'))  # Updated to match new function name
                
            except Exception as e:
                logger.error(f'Checkout error: {str(e)}')
                db.session.rollback()
                flash('Error processing your order', 'error')
        
        total_price = sum(item.menu_item.price * item.quantity for item in cart_items)
        return render_template('customer/checkout.html', 
                               cart_items=cart_items, 
                               total_price=total_price,
                               user_address=current_user.address)

    # Customer Orders (Order History)
    @app.route('/customer/orders')
    @login_required
    @role_required('customer')
    def order_history():  # Changed function name to match template
        orders = Order.query.filter_by(
            customer_id=current_user.id
        ).order_by(Order.created_at.desc()).all()
        return render_template('customer/orders.html', orders=orders)

    # Order Details
    @app.route('/customer/order/<int:order_id>')
    @login_required
    @role_required('customer')
    def order_details(order_id):
        order = Order.query.get_or_404(order_id)
        
        if order.customer_id != current_user.id:
            flash('Unauthorized access', 'error')
            return redirect(url_for('order_history'))  # Updated to match new function name
        
        return render_template('customer/order_details.html', order=order)

    # Add/Remove Favorite
    @app.route('/customer/favorite/<int:restaurant_id>')
    @login_required
    @role_required('customer')
    def toggle_favorite(restaurant_id):
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        favorite = Favorite.query.filter_by(
            customer_id=current_user.id, 
            restaurant_id=restaurant_id
        ).first()
        
        if favorite:
            db.session.delete(favorite)
            flash(f'{restaurant.name} removed from favorites', 'info')
        else:
            favorite = Favorite(
                customer_id=current_user.id,
                restaurant_id=restaurant_id
            )
            db.session.add(favorite)
            flash(f'{restaurant.name} added to favorites', 'success')
        
        db.session.commit()
        return redirect(request.referrer or url_for('browse_restaurants'))

    # Add Review
    @app.route('/customer/review/<int:restaurant_id>', methods=['POST'])
    @login_required
    @role_required('customer')
    def add_review(restaurant_id):
        try:
            rating = int(request.form.get('rating'))
            comment = request.form.get('comment', '')
            
            # Check if user has ordered from this restaurant
            has_ordered = Order.query.filter_by(
                customer_id=current_user.id,
                restaurant_id=restaurant_id
            ).first()
            
            if not has_ordered:
                flash('You can only review restaurants you have ordered from', 'error')
                return redirect(request.referrer)
            
            # Check if user already reviewed this restaurant
            existing_review = Review.query.filter_by(
                customer_id=current_user.id,
                restaurant_id=restaurant_id
            ).first()
            
            if existing_review:
                existing_review.rating = rating
                existing_review.comment = comment
                flash('Review updated successfully', 'success')
            else:
                review = Review(
                    customer_id=current_user.id,
                    restaurant_id=restaurant_id,
                    rating=rating,
                    comment=comment
                )
                db.session.add(review)
                flash('Review added successfully', 'success')
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f'Add review error: {str(e)}')
            flash('Error adding review', 'error')
            
        return redirect(request.referrer or url_for('browse_restaurants'))

    # Customer Profile
    @app.route('/customer/profile', methods=['GET', 'POST'])
    @login_required
    @role_required('customer')
    def customer_profile():
        if request.method == 'POST':
            try:
                current_user.phone = request.form.get('phone', '')
                current_user.address = request.form.get('address', '')
                current_user.dietary_restrictions = request.form.get('dietary_restrictions', '')
                
                # Update password if provided
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                if current_password and new_password:
                    if check_password_hash(current_user.password_hash, current_password):
                        current_user.password_hash = generate_password_hash(new_password)
                        flash('Password updated successfully', 'success')
                    else:
                        flash('Current password is incorrect', 'error')
                        return render_template('customer/profile.html')
                
                db.session.commit()
                flash('Profile updated successfully', 'success')
                
            except Exception as e:
                logger.error(f'Profile update error: {str(e)}')
                flash('Error updating profile', 'error')
        
        return render_template('customer/profile.html')


# -----------------------------
# Restaurant Owner Routes
# -----------------------------
def register_restaurant_routes(app):

    @app.route('/restaurant/dashboard')
    @login_required
    @role_required('restaurant_owner')
    def restaurant_dashboard():
        restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
        total_orders = Order.query.join(Restaurant).filter(
            Restaurant.owner_id == current_user.id).count()
        pending_orders = Order.query.join(Restaurant).filter(
            Restaurant.owner_id == current_user.id, Order.status == 'pending').count()
        recent_orders = Order.query.join(Restaurant).filter(
            Restaurant.owner_id == current_user.id).order_by(Order.created_at.desc()).limit(10).all()
        
        # Calculate revenue
        total_revenue = db.session.query(func.sum(Order.total_amount)).join(Restaurant).filter(
            Restaurant.owner_id == current_user.id,
            Order.status == 'delivered'
        ).scalar() or 0
        
        return render_template('restaurant/dashboard.html',
                               restaurants=restaurants,
                               total_orders=total_orders,
                               pending_orders=pending_orders,
                               recent_orders=recent_orders,
                               total_revenue=total_revenue)

    # Restaurant Management
    @app.route('/restaurant/manage', methods=['GET', 'POST'])
    @login_required
    @role_required('restaurant_owner')
    def manage_restaurant():
        restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
        
        if request.method == 'POST':
            try:
                name = request.form.get('name')
                cuisine_type = request.form.get('cuisine_type')
                address = request.form.get('address')
                phone = request.form.get('phone')
                description = request.form.get('description', '')
                
                restaurant = Restaurant(
                    name=name,
                    cuisine_type=cuisine_type,
                    address=address,
                    phone=phone,
                    description=description,
                    owner_id=current_user.id,
                    is_active=True
                )
                
                db.session.add(restaurant)
                db.session.commit()
                flash('Restaurant added successfully!', 'success')
                return redirect(url_for('manage_restaurant'))
                
            except Exception as e:
                logger.error(f'Restaurant creation error: {str(e)}')
                flash('Error creating restaurant', 'error')
        
        return render_template('restaurant/manage_restaurant.html', restaurants=restaurants)

    # Menu Management
    @app.route('/restaurant/menu')
    @login_required
    @role_required('restaurant_owner')
    def restaurant_menu_management():
        restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
        restaurant_id = request.args.get('restaurant_id')
        selected_restaurant = None
        menu_items = []

        if restaurant_id:
            selected_restaurant = Restaurant.query.filter_by(
                id=restaurant_id, owner_id=current_user.id
            ).first()
            if selected_restaurant:
                menu_items = MenuItem.query.filter_by(
                    restaurant_id=selected_restaurant.id
                ).all()
        elif restaurants:
            selected_restaurant = restaurants[0]
            menu_items = MenuItem.query.filter_by(
                restaurant_id=selected_restaurant.id
            ).all()

        return render_template('restaurant/menu_management.html',
                               restaurants=restaurants,
                               selected_restaurant=selected_restaurant,
                               menu_items=menu_items)

    # Add Menu Item
    @app.route('/restaurant/menu/add', methods=['POST'])
    @login_required
    @role_required('restaurant_owner')
    def add_menu_item():
        try:
            restaurant_id = request.form.get('restaurant_id')
            restaurant = Restaurant.query.filter_by(
                id=restaurant_id, owner_id=current_user.id
            ).first()
            
            if not restaurant:
                flash('Restaurant not found', 'error')
                return redirect(url_for('restaurant_menu_management'))
            
            menu_item = MenuItem(
                restaurant_id=restaurant_id,
                name=request.form.get('name'),
                description=request.form.get('description', ''),
                price=float(request.form.get('price')),
                category=request.form.get('category'),
                is_available=True
            )
            
            db.session.add(menu_item)
            db.session.commit()
            flash('Menu item added successfully!', 'success')
            
        except Exception as e:
            logger.error(f'Add menu item error: {str(e)}')
            flash('Error adding menu item', 'error')
        
        return redirect(url_for('restaurant_menu_management'))

    # Update Menu Item
    @app.route('/restaurant/menu/update/<int:item_id>', methods=['POST'])
    @login_required
    @role_required('restaurant_owner')
    def update_menu_item(item_id):
        try:
            menu_item = MenuItem.query.join(Restaurant).filter(
                MenuItem.id == item_id,
                Restaurant.owner_id == current_user.id
            ).first()
            
            if not menu_item:
                flash('Menu item not found', 'error')
                return redirect(url_for('restaurant_menu_management'))
            
            menu_item.name = request.form.get('name')
            menu_item.description = request.form.get('description', '')
            menu_item.price = float(request.form.get('price'))
            menu_item.category = request.form.get('category')
            menu_item.is_available = 'is_available' in request.form
            
            db.session.commit()
            flash('Menu item updated successfully!', 'success')
            
        except Exception as e:
            logger.error(f'Update menu item error: {str(e)}')
            flash('Error updating menu item', 'error')
        
        return redirect(url_for('restaurant_menu_management'))

    # Delete Menu Item
    @app.route('/restaurant/menu/delete/<int:item_id>')
    @login_required
    @role_required('restaurant_owner')
    def delete_menu_item(item_id):
        try:
            menu_item = MenuItem.query.join(Restaurant).filter(
                MenuItem.id == item_id,
                Restaurant.owner_id == current_user.id
            ).first()
            
            if menu_item:
                db.session.delete(menu_item)
                db.session.commit()
                flash('Menu item deleted successfully!', 'success')
            else:
                flash('Menu item not found', 'error')
                
        except Exception as e:
            logger.error(f'Delete menu item error: {str(e)}')
            flash('Error deleting menu item', 'error')
        
        return redirect(url_for('restaurant_menu_management'))

    # Order Management
    @app.route('/restaurant/orders')
    @login_required
    @role_required('restaurant_owner')
    def restaurant_orders():
        status_filter = request.args.get('status', '')
        
        query = Order.query.join(Restaurant).filter(Restaurant.owner_id == current_user.id)
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        orders = query.order_by(Order.created_at.desc()).all()
        return render_template('restaurant/orders.html', orders=orders, status_filter=status_filter)

    # Update Order Status
    @app.route('/restaurant/order/<int:order_id>/status', methods=['POST'])
    @login_required
    @role_required('restaurant_owner')
    def update_order_status(order_id):
        try:
            order = Order.query.join(Restaurant).filter(
                Order.id == order_id,
                Restaurant.owner_id == current_user.id
            ).first()
            
            if not order:
                flash('Order not found', 'error')
                return redirect(url_for('restaurant_orders'))
            
            new_status = request.form.get('status')
            valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled']
            
            if new_status in valid_statuses:
                order.status = new_status
                db.session.commit()
                flash(f'Order status updated to {new_status}', 'success')
            else:
                flash('Invalid status', 'error')
                
        except Exception as e:
            logger.error(f'Update order status error: {str(e)}')
            flash('Error updating order status', 'error')
        
        return redirect(url_for('restaurant_orders'))

    # Restaurant Analytics
    @app.route('/restaurant/analytics')
    @login_required
    @role_required('restaurant_owner')
    def restaurant_analytics():
        restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
        
        # Get analytics data
        orders_by_status = db.session.query(
            Order.status, func.count(Order.id)
        ).join(Restaurant).filter(
            Restaurant.owner_id == current_user.id
        ).group_by(Order.status).all()
        
        # Revenue by month
        revenue_by_month = db.session.query(
            func.date_trunc('month', Order.created_at).label('month'),
            func.sum(Order.total_amount).label('revenue')
        ).join(Restaurant).filter(
            Restaurant.owner_id == current_user.id,
            Order.status == 'delivered'
        ).group_by('month').order_by('month').all()
        
        # Popular items
        popular_items = db.session.query(
            MenuItem.name, func.sum(OrderItem.quantity).label('total_ordered')
        ).join(OrderItem).join(Order).join(Restaurant).filter(
            Restaurant.owner_id == current_user.id
        ).group_by(MenuItem.name).order_by(desc('total_ordered')).limit(10).all()
        
        return render_template('restaurant/analytics.html',
                               restaurants=restaurants,
                               orders_by_status=orders_by_status,
                               revenue_by_month=revenue_by_month,
                               popular_items=popular_items)


# -----------------------------
# API Routes
# -----------------------------
def register_api_routes(app):
    
    @app.route('/api/restaurants')
    def api_restaurants():
        restaurants = Restaurant.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': r.id,
            'name': r.name,
            'cuisine_type': r.cuisine_type,
            'address': r.address,
            'rating': r.rating
        } for r in restaurants])
    
    @app.route('/api/restaurant/<int:restaurant_id>/menu')
    def api_restaurant_menu(restaurant_id):
        menu_items = MenuItem.query.filter_by(
            restaurant_id=restaurant_id, is_available=True
        ).all()
        return jsonify([{
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': float(item.price),
            'category': item.category
        } for item in menu_items])


# -----------------------------
# Helper Functions
# -----------------------------
def get_recommendations(customer_id):
    """Simple recommendations based on past orders and ratings"""
    # Get restaurants from recent orders
    recent_orders = Order.query.filter_by(customer_id=customer_id).limit(10).all()
    if recent_orders:
        restaurant_ids = list(set([order.restaurant_id for order in recent_orders]))
        # Get similar restaurants (same cuisine type)
        cuisines = db.session.query(Restaurant.cuisine_type).filter(
            Restaurant.id.in_(restaurant_ids)
        ).distinct().all()
        cuisine_list = [c[0] for c in cuisines]
        
        recommendations = Restaurant.query.filter(
            Restaurant.cuisine_type.in_(cuisine_list),
            ~Restaurant.id.in_(restaurant_ids),
            Restaurant.is_active == True
        ).order_by(Restaurant.rating.desc()).limit(3).all()
        
        if len(recommendations) < 3:
            # Fill with top-rated restaurants
            additional = Restaurant.query.filter(
                Restaurant.is_active == True,
                ~Restaurant.id.in_([r.id for r in recommendations] + restaurant_ids)
            ).order_by(Restaurant.rating.desc()).limit(3 - len(recommendations)).all()
            recommendations.extend(additional)
    else:
        # New user - show top-rated restaurants
        recommendations = Restaurant.query.filter_by(
            is_active=True
        ).order_by(Restaurant.rating.desc()).limit(3).all()
    
    return recommendations


# -----------------------------
# Main Registration Function
# -----------------------------
def register_all_routes(app):
    """Register all routes with the Flask application"""
    register_routes(app)
    register_restaurant_routes(app)
    register_api_routes(app)