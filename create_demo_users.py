#!/usr/bin/env python3
"""
Script to create demo users for the JustEat application
"""

from app import create_app, db
from models import User, Restaurant, MenuItem
from werkzeug.security import generate_password_hash

def create_demo_users():
    """Create demo users and restaurants for testing"""
    app = create_app()
    
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("Database tables created.")
        
        # Check if users already exist
        try:
            if User.query.first():
                print("Demo users already exist!")
                return
        except Exception:
            # Tables might not exist yet, continue with creation
            pass
        
        print("Creating demo users...")
        
        # Create customer users
        customers = [
            {
                'username': 'adi',
                'email': 'john@example.com',
                'password': 'password123',
                'role': 'customer',
                'phone': '+1234567890',
                'address': '123 Main St, City, State',
                'dietary_restrictions': 'No nuts'
            },
            {
                'username': 'jane_smith',
                'email': 'jane@example.com',
                'password': 'password123',
                'role': 'customer',
                'phone': '+1234567891',
                'address': '456 Oak Ave, City, State',
                'dietary_restrictions': 'Vegetarian'
            }
        ]
        
        # Create restaurant owner users
        restaurant_owners = [
            {
                'username': 'pizza_palace_owner',
                'email': 'owner@pizzapalace.com',
                'password': 'password123',
                'role': 'restaurant_owner'
            },
            {
                'username': 'burger_barn_owner',
                'email': 'owner@burgerbarn.com',
                'password': 'password123',
                'role': 'restaurant_owner'
            },
            {
                'username': 'sushi_spot_owner',
                'email': 'owner@sushispot.com',
                'password': 'password123',
                'role': 'restaurant_owner'
            }
        ]
        
        # Add all users to database
        all_users = customers + restaurant_owners
        user_objects = []
        
        for user_data in all_users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                role=user_data['role'],
                phone=user_data.get('phone'),
                address=user_data.get('address'),
                dietary_restrictions=user_data.get('dietary_restrictions')
            )
            db.session.add(user)
            user_objects.append(user)
            print(f"Created user: {user.username} ({user.role})")
        
        db.session.flush()
        
        # Create restaurants
        restaurants_data = [
            {
                'name': 'Pizza Palace',
                'description': 'Authentic Italian pizzas with fresh ingredients',
                'cuisine_type': 'Italian',
                'address': '789 Pizza St, City, State',
                'phone': '+1234567892',
                'image_url': '/static/images/pizza_palace.jpg',
                'rating': 4.5,
                'delivery_time': 25,
                'delivery_fee': 2.99,
                'minimum_order': 15.0,
                'owner_username': 'pizza_palace_owner'
            },
            {
                'name': 'Burger Barn',
                'description': 'Juicy burgers and crispy fries',
                'cuisine_type': 'American',
                'address': '321 Burger Blvd, City, State',
                'phone': '+1234567893',
                'image_url': '/static/images/burger_barn.jpg',
                'rating': 4.2,
                'delivery_time': 20,
                'delivery_fee': 1.99,
                'minimum_order': 12.0,
                'owner_username': 'burger_barn_owner'
            },
            {
                'name': 'Sushi Spot',
                'description': 'Fresh sushi and Japanese cuisine',
                'cuisine_type': 'Japanese',
                'address': '654 Sushi Ave, City, State',
                'phone': '+1234567894',
                'image_url': '/static/images/sushi_spot.jpg',
                'rating': 4.8,
                'delivery_time': 35,
                'delivery_fee': 3.99,
                'minimum_order': 20.0,
                'owner_username': 'sushi_spot_owner'
            }
        ]
        
        restaurant_objects = []
        for rest_data in restaurants_data:
            owner = next(u for u in user_objects if u.username == rest_data['owner_username'])
            restaurant = Restaurant(
                name=rest_data['name'],
                description=rest_data['description'],
                cuisine_type=rest_data['cuisine_type'],
                address=rest_data['address'],
                phone=rest_data['phone'],
                image_url=rest_data['image_url'],
                rating=rest_data['rating'],
                delivery_time=rest_data['delivery_time'],
                delivery_fee=rest_data['delivery_fee'],
                minimum_order=rest_data['minimum_order'],
                owner_id=owner.id,
                is_active=True
            )
            db.session.add(restaurant)
            restaurant_objects.append(restaurant)
            print(f"Created restaurant: {restaurant.name}")
        
        db.session.flush()
        
        # Create menu items
        menu_items_data = [
            # Pizza Palace menu
            {'name': 'Margherita Pizza', 'description': 'Classic tomato sauce, mozzarella, and basil', 'price': 14.99, 'category': 'Pizza', 'restaurant': 'Pizza Palace', 'is_vegetarian': True},
            {'name': 'Pepperoni Pizza', 'description': 'Tomato sauce, mozzarella, and pepperoni', 'price': 16.99, 'category': 'Pizza', 'restaurant': 'Pizza Palace'},
            {'name': 'Caesar Salad', 'description': 'Romaine lettuce, parmesan, croutons, caesar dressing', 'price': 9.99, 'category': 'Salad', 'restaurant': 'Pizza Palace', 'is_vegetarian': True},
            {'name': 'Garlic Bread', 'description': 'Fresh baked bread with garlic butter', 'price': 5.99, 'category': 'Appetizer', 'restaurant': 'Pizza Palace', 'is_vegetarian': True},
            
            # Burger Barn menu
            {'name': 'Classic Burger', 'description': 'Beef patty, lettuce, tomato, onion, pickles', 'price': 12.99, 'category': 'Burger', 'restaurant': 'Burger Barn'},
            {'name': 'Bacon Cheeseburger', 'description': 'Beef patty, bacon, cheese, lettuce, tomato', 'price': 15.99, 'category': 'Burger', 'restaurant': 'Burger Barn'},
            {'name': 'Veggie Burger', 'description': 'Plant-based patty, lettuce, tomato, avocado', 'price': 13.99, 'category': 'Burger', 'restaurant': 'Burger Barn', 'is_vegetarian': True},
            {'name': 'French Fries', 'description': 'Crispy golden fries', 'price': 4.99, 'category': 'Side', 'restaurant': 'Burger Barn', 'is_vegetarian': True},
            
            # Sushi Spot menu
            {'name': 'California Roll', 'description': 'Crab, avocado, cucumber', 'price': 8.99, 'category': 'Roll', 'restaurant': 'Sushi Spot'},
            {'name': 'Salmon Nigiri', 'description': 'Fresh salmon over seasoned rice', 'price': 6.99, 'category': 'Nigiri', 'restaurant': 'Sushi Spot'},
            {'name': 'Vegetable Tempura', 'description': 'Assorted vegetables in light tempura batter', 'price': 9.99, 'category': 'Appetizer', 'restaurant': 'Sushi Spot', 'is_vegetarian': True},
            {'name': 'Miso Soup', 'description': 'Traditional soybean paste soup', 'price': 3.99, 'category': 'Soup', 'restaurant': 'Sushi Spot', 'is_vegetarian': True}
        ]
        
        for item_data in menu_items_data:
            restaurant = next(r for r in restaurant_objects if r.name == item_data['restaurant'])
            menu_item = MenuItem(
                name=item_data['name'],
                description=item_data['description'],
                price=item_data['price'],
                category=item_data['category'],
                restaurant_id=restaurant.id,
                is_vegetarian=item_data.get('is_vegetarian', False),
                is_available=True
            )
            db.session.add(menu_item)
            print(f"Created menu item: {menu_item.name} for {restaurant.name}")
        
        db.session.commit()
        print("\n✅ Demo users, restaurants, and menu items created successfully!")
        print("\nDemo Accounts:")
        print("Customers:")
        print("  - Username: adi, Password: password123")
        print("  - Username: jane_smith, Password: password123")
        print("\nRestaurant Owners:")
        print("  - Username: pizza_palace_owner, Password: password123")
        print("  - Username: burger_barn_owner, Password: password123")
        print("  - Username: sushi_spot_owner, Password: password123")

if __name__ == '__main__':
    create_demo_users()
