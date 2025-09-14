from flask import render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import or_, func
import json
import logging

logger = logging.getLogger(__name__)

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

def register_routes(app):
    # Import models within the function to avoid circular imports
    from models import User, Restaurant, MenuItem, Order, OrderItem, Review, Favorite, Cart

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'customer':
                return redirect(url_for('customer_dashboard'))
            else:
                return redirect(url_for('restaurant_dashboard'))
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            try:
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')
                
                logger.info(f'Login attempt for username: {username}')
                
                if not username or not password:
                    flash('Please enter both username and password', 'error')
                    return render_template('login.html')
                
                user = User.query.filter_by(username=username).first()
                logger.info(f'User found in database: {user is not None}')
                
                if user:
                    password_valid = check_password_hash(user.password_hash, password)
                    logger.info(f'Password valid for {username}: {password_valid}')
                    
                    if password_valid:
                        login_result = login_user(user, remember=True)
                        logger.info(f'Flask-Login login_user result: {login_result}')
                        logger.info(f'User {username} logged in successfully')
                        flash('Login successful!', 'success')
                        
                        if user.role == 'customer':
                            return redirect(url_for('customer_dashboard'))
                        else:
                            return redirect(url_for('restaurant_dashboard'))
                    else:
                        flash('Invalid username or password', 'error')
                        logger.warning(f'Invalid password for username: {username}')
                else:
                    flash('Invalid username or password', 'error')
                    logger.warning(f'Username not found: {username}')
            except Exception as e:
                logger.error(f'Login error: {str(e)}')
                flash('An error occurred during login', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        username = current_user.username
        logout_user()
        logger.info(f'User {username} logged out')
        flash('You have been logged out', 'info')
        return redirect(url_for('index'))

    @app.route('/reset-password', methods=['GET', 'POST'])
    def reset_password():
        if request.method == 'POST':
            try:
                email = request.form['email']
                user = User.query.filter_by(email=email).first()
                
                if user:
                    # In a real application, you would send an email with reset link
                    flash('Password reset instructions have been sent to your email', 'info')
                    logger.info(f'Password reset requested for email: {email}')
                else:
                    flash('Email not found', 'error')
            except Exception as e:
                logger.error(f'Password reset error: {str(e)}')
                flash('An error occurred', 'error')
        
        return render_template('reset_password.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            try:
                username = request.form['username']
                email = request.form['email']
                password = request.form['password']
                confirm_password = request.form['confirm_password']
                role = request.form.get('role', 'customer')
                
                # Validation
                if not username or not email or not password:
                    flash('All fields are required', 'error')
                    return render_template('signup.html')
                
                if password != confirm_password:
                    flash('Passwords do not match', 'error')
                    return render_template('signup.html')
                
                if len(password) < 6:
                    flash('Password must be at least 6 characters long', 'error')
                    return render_template('signup.html')
                
                # Check if user already exists
                if User.query.filter_by(username=username).first():
                    flash('Username already exists', 'error')
                    return render_template('signup.html')
                
                if User.query.filter_by(email=email).first():
                    flash('Email already registered', 'error')
                    return render_template('signup.html')
                
                # Create new user
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password),
                    role=role
                )
                
                # Add customer-specific fields if role is customer
                if role == 'customer':
                    user.phone = request.form.get('phone', '')
                    user.address = request.form.get('address', '')
                    user.dietary_restrictions = request.form.get('dietary_restrictions', '')
                
                db.session.add(user)
                db.session.commit()
                
                logger.info(f'New user registered: {username} ({role})')
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                logger.error(f'Signup error: {str(e)}')
                flash('An error occurred during registration', 'error')
        
        return render_template('signup.html')

    @app.route('/debug/auth')
    def debug_auth():
        """Debug route to check authentication status"""
        from flask_login import current_user
        info = {
            'is_authenticated': current_user.is_authenticated,
            'user_id': getattr(current_user, 'id', None),
            'username': getattr(current_user, 'username', None),
            'role': getattr(current_user, 'role', None),
            'total_users': User.query.count()
        }
        return f"<pre>{info}</pre>"

    # Customer Routes
    @app.route('/customer/dashboard')
    @login_required
    @role_required('customer')
    def customer_dashboard():
        try:
            restaurants = Restaurant.query.filter_by(is_active=True).all()
            favorites = [fav.restaurant for fav in current_user.favorites]
            recent_orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
            
            # Get recommendations based on order history
            recommendations = get_recommendations(current_user.id)
            
            return render_template('customer/dashboard.html', 
                                 restaurants=restaurants, 
                                 favorites=favorites,
                                 recent_orders=recent_orders,
                                 recommendations=recommendations)
        except Exception as e:
            logger.error(f'Customer dashboard error: {str(e)}')
            flash('An error occurred loading the dashboard', 'error')
            return render_template('customer/dashboard.html', restaurants=[], favorites=[], recent_orders=[])

    @app.route('/customer/restaurants')
    @login_required
    @role_required('customer')
    def browse_restaurants():
        try:
            search = request.args.get('search', '')
            cuisine = request.args.get('cuisine', '')
            sort_by = request.args.get('sort', 'rating')
            
            query = Restaurant.query.filter_by(is_active=True)
            
            if search:
                query = query.filter(or_(
                    Restaurant.name.contains(search),
                    Restaurant.cuisine_type.contains(search),
                    Restaurant.address.contains(search)
                ))
            
            if cuisine:
                query = query.filter_by(cuisine_type=cuisine)
            
            if sort_by == 'rating':
                query = query.order_by(Restaurant.rating.desc())
            elif sort_by == 'delivery_time':
                query = query.order_by(Restaurant.delivery_time.asc())
            elif sort_by == 'delivery_fee':
                query = query.order_by(Restaurant.delivery_fee.asc())
            
            restaurants = query.all()
            cuisines = db.session.query(Restaurant.cuisine_type).distinct().all()
            cuisines = [c[0] for c in cuisines]
            
            return render_template('customer/restaurants.html', 
                                 restaurants=restaurants, 
                             cuisines=cuisines,
                             current_search=search,
                             current_cuisine=cuisine,
                             current_sort=sort_by)
        except Exception as e:
            logger.error(f'Browse restaurants error: {str(e)}')
            flash('An error occurred loading restaurants', 'error')
            return render_template('customer/restaurants.html', restaurants=[], cuisines=[])

    @app.route('/customer/restaurant/<int:restaurant_id>')
    @login_required
    @role_required('customer')
    def restaurant_menu(restaurant_id):
        try:
            restaurant = Restaurant.query.get_or_404(restaurant_id)
            menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id, is_available=True).all()
            
            # Group menu items by category
            categories = {}
            for item in menu_items:
                if item.category not in categories:
                    categories[item.category] = []
                categories[item.category].append(item)
            
            # Check if restaurant is in favorites
            is_favorite = Favorite.query.filter_by(customer_id=current_user.id, restaurant_id=restaurant_id).first() is not None
            
            # Get reviews
            reviews = Review.query.filter_by(restaurant_id=restaurant_id).order_by(Review.created_at.desc()).limit(10).all()
            
            return render_template('customer/restaurant_menu.html', 
                                 restaurant=restaurant, 
                                 categories=categories,
                             is_favorite=is_favorite,
                             reviews=reviews)
        except Exception as e:
            logger.error(f'Restaurant menu error: {str(e)}')
            flash('An error occurred loading the menu', 'error')
            return redirect(url_for('browse_restaurants'))

    # Add a simple helper function for recommendations
    def get_recommendations(user_id):
        # Simple recommendation based on order history
        recent_orders = Order.query.filter_by(customer_id=user_id).limit(5).all()
        if recent_orders:
            # Get restaurants from recent orders
            restaurant_ids = [order.restaurant_id for order in recent_orders]
            return Restaurant.query.filter(Restaurant.id.in_(restaurant_ids)).limit(3).all()
        else:
            # Return popular restaurants if no order history
            return Restaurant.query.filter_by(is_active=True).order_by(Restaurant.rating.desc()).limit(3).all()

    @app.route('/customer/add-to-cart', methods=['POST'])
    @login_required
    @role_required('customer')
    def add_to_cart():
        try:
            data = request.get_json()
            menu_item_id = data.get('menu_item_id')
            quantity = data.get('quantity', 1)
            special_instructions = data.get('special_instructions', '')
            
            menu_item = MenuItem.query.get_or_404(menu_item_id)
            
            # Check if item already in cart
            cart_item = Cart.query.filter_by(customer_id=current_user.id, menu_item_id=menu_item_id).first()
            
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = Cart(
                    customer_id=current_user.id,
                    menu_item_id=menu_item_id,
                    quantity=quantity,
                    special_instructions=special_instructions
                )
                db.session.add(cart_item)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Item added to cart'})
        except Exception as e:
            logger.error(f'Add to cart error: {str(e)}')
            return jsonify({'success': False, 'message': 'Error adding item to cart'})

    @app.route('/customer/cart')
    @login_required
    @role_required('customer')
    def view_cart():
        try:
            cart_items = Cart.query.filter_by(customer_id=current_user.id).all()
            
            total = 0
            restaurant_items = {}
            
            for item in cart_items:
                restaurant = item.menu_item.restaurant
                if restaurant.id not in restaurant_items:
                    restaurant_items[restaurant.id] = {
                        'restaurant': restaurant,
                        'items': [],
                        'subtotal': 0
                    }
                
                item_total = item.menu_item.price * item.quantity
                restaurant_items[restaurant.id]['items'].append(item)
                restaurant_items[restaurant.id]['subtotal'] += item_total
                total += item_total
            
            return render_template('customer/cart.html', 
                                 restaurant_items=restaurant_items,
                                 total=total)
        except Exception as e:
            logger.error(f'View cart error: {str(e)}')
            flash('An error occurred loading your cart', 'error')
            return render_template('customer/cart.html', restaurant_items={}, total=0)

    @app.route('/customer/place-order', methods=['POST'])
    @login_required
    @role_required('customer')
    def place_order():
        try:
            data = request.get_json()
            restaurant_id = data.get('restaurant_id')
            notes = data.get('notes', '')
            
            # Get cart items for this restaurant
            cart_items = Cart.query.join(MenuItem).filter(
                Cart.customer_id == current_user.id,
                MenuItem.restaurant_id == restaurant_id
            ).all()
            
            if not cart_items:
                return jsonify({'success': False, 'message': 'No items in cart for this restaurant'})
            
            # Create order
            order = Order(
                customer_id=current_user.id,
                restaurant_id=restaurant_id,
                notes=notes,
                status='pending'
            )
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Create order items and remove from cart
            total = 0
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=cart_item.menu_item_id,
                    quantity=cart_item.quantity,
                    price=cart_item.menu_item.price,
                    special_instructions=cart_item.special_instructions
                )
                db.session.add(order_item)
                total += cart_item.menu_item.price * cart_item.quantity
                db.session.delete(cart_item)
            
            order.total_amount = total
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Order placed successfully', 'order_id': order.id})
        except Exception as e:
            logger.error(f'Place order error: {str(e)}')
            return jsonify({'success': False, 'message': 'Error placing order'})

    @app.route('/customer/orders')
    @login_required
    @role_required('customer')
    def order_history():
        try:
            orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
            return render_template('customer/orders.html', orders=orders)
        except Exception as e:
            logger.error(f'Order history error: {str(e)}')
            flash('An error occurred loading your orders', 'error')
            return render_template('customer/orders.html', orders=[])

    @app.route('/customer/order/<int:order_id>')
    @login_required
    @role_required('customer')
    def order_details(order_id):
        try:
            order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
            return render_template('customer/order_details.html', order=order)
        except Exception as e:
            logger.error(f'Order details error: {str(e)}')
            flash('Order not found', 'error')
            return redirect(url_for('order_history'))

    # API Routes
    @app.route('/api/cart/count')
    def cart_count():
        try:
            if not current_user.is_authenticated:
                return jsonify({'count': 0})
            count = Cart.query.filter_by(customer_id=current_user.id).count()
            return jsonify({'count': count})
        except Exception as e:
            logger.error(f'Cart count error: {str(e)}')
            return jsonify({'count': 0})

# Restaurant Owner Routes
def register_restaurant_routes(app):
    @app.route('/restaurant/dashboard')
    @login_required
    @role_required('restaurant_owner')
    def restaurant_dashboard():
        try:
            restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
            
            # Get statistics
            total_orders = Order.query.join(Restaurant).filter(Restaurant.owner_id == current_user.id).count()
            pending_orders = Order.query.join(Restaurant).filter(
                Restaurant.owner_id == current_user.id,
                Order.status == 'pending'
            ).count()
            
            # Get recent orders
            recent_orders = Order.query.join(Restaurant).filter(
                Restaurant.owner_id == current_user.id
            ).order_by(Order.created_at.desc()).limit(10).all()
            
            return render_template('restaurant/dashboard.html', 
                                 restaurants=restaurants,
                                 total_orders=total_orders,
                                 pending_orders=pending_orders,
                                 recent_orders=recent_orders)
        except Exception as e:
            logger.error(f'Restaurant dashboard error: {str(e)}')
            flash('An error occurred loading the dashboard', 'error')
            return render_template('restaurant/dashboard.html', 
                                 restaurants=[],
                                 total_orders=0,
                                 pending_orders=0,
                                 recent_orders=[])

    @app.route('/restaurant/orders')
    @login_required
    @role_required('restaurant_owner')
    def restaurant_orders():
        try:
            status_filter = request.args.get('status', '')
            page = request.args.get('page', 1, type=int)
            
            query = Order.query.join(Restaurant).filter(Restaurant.owner_id == current_user.id)
            
            if status_filter:
                query = query.filter(Order.status == status_filter)
            
            orders = query.order_by(Order.created_at.desc()).paginate(
                page=page, per_page=20, error_out=False
            )
            
            return render_template('restaurant/orders.html', orders=orders, status_filter=status_filter)
        except Exception as e:
            logger.error(f'Restaurant orders error: {str(e)}')
            flash('An error occurred loading orders', 'error')
            return render_template('restaurant/orders.html', orders=None, status_filter='')

    @app.route('/restaurant/menu')
    @login_required
    @role_required('restaurant_owner')
    def restaurant_menu_management():
        try:
            restaurant_id = request.args.get('restaurant_id')
            restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
            
            if restaurant_id:
                restaurant = Restaurant.query.filter_by(id=restaurant_id, owner_id=current_user.id).first()
                if restaurant:
                    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
                    return render_template('restaurant/menu_management.html', 
                                         restaurants=restaurants, 
                                         selected_restaurant=restaurant,
                                         menu_items=menu_items)
            
            return render_template('restaurant/menu_management.html', restaurants=restaurants)
        except Exception as e:
            logger.error(f'Menu management error: {str(e)}')
            flash('An error occurred loading menu management', 'error')
            return render_template('restaurant/menu_management.html', restaurants=[])

    @app.route('/api/orders/update-status', methods=['POST'])
    @login_required
    @role_required('restaurant_owner')
    def update_order_status():
        try:
            data = request.get_json()
            order_id = data.get('order_id')
            new_status = data.get('status')
            
            order = Order.query.join(Restaurant).filter(
                Order.id == order_id,
                Restaurant.owner_id == current_user.id
            ).first()
            
            if not order:
                return jsonify({'success': False, 'message': 'Order not found'})
            
            order.status = new_status
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Order status updated'})
        except Exception as e:
            logger.error(f'Update order status error: {str(e)}')
            return jsonify({'success': False, 'message': 'Failed to update order status'})

    # End of register_restaurant_routes function

# Helper function for recommendations
def get_recommendations(customer_id):
    """Get smart recommendations for a customer based on order history and preferences"""
    try:
        # Get customer's order history
        recent_orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.created_at.desc()).limit(10).all()
        
        if not recent_orders:
            # New customer - return popular items
            popular_items = MenuItem.query.filter_by(is_available=True).order_by(MenuItem.id.desc()).limit(5).all()
            return popular_items
        
        # Get frequently ordered categories
        category_counts = {}
        for order in recent_orders:
            for item in order.order_items:
                category = item.menu_item.category
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get top categories
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Get recommendations from top categories
        recommendations = []
        for category, _ in top_categories:
            items = MenuItem.query.filter_by(category=category, is_available=True).limit(2).all()
            recommendations.extend(items)
        
        return recommendations[:5]
    except Exception as e:
        logger.error(f'Get recommendations error: {str(e)}')
        return []
