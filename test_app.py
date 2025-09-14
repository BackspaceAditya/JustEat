import unittest
import json
from app import app, db
from models import User, Restaurant, MenuItem, Order, OrderItem, Review, Favorite, Cart
from werkzeug.security import generate_password_hash

class JustEatTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test users
        self.customer = User(
            username='test_customer',
            email='customer@test.com',
            password_hash=generate_password_hash('password123'),
            role='customer'
        )
        
        self.restaurant_owner = User(
            username='test_owner',
            email='owner@test.com',
            password_hash=generate_password_hash('password123'),
            role='restaurant_owner'
        )
        
        db.session.add(self.customer)
        db.session.add(self.restaurant_owner)
        db.session.commit()
        
        # Create test restaurant
        self.restaurant = Restaurant(
            name='Test Restaurant',
            description='A test restaurant',
            cuisine_type='Italian',
            address='123 Test St',
            phone='+1234567890',
            rating=4.5,
            delivery_time=30,
            delivery_fee=2.99,
            minimum_order=15.0,
            owner_id=self.restaurant_owner.id
        )
        
        db.session.add(self.restaurant)
        db.session.commit()
        
        # Create test menu item
        self.menu_item = MenuItem(
            name='Test Pizza',
            description='Delicious test pizza',
            price=12.99,
            category='Pizza',
            restaurant_id=self.restaurant.id,
            is_vegetarian=True
        )
        
        db.session.add(self.menu_item)
        db.session.commit()

    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login_customer(self):
        """Helper method to log in as customer."""
        return self.app.post('/login', data={
            'username': 'test_customer',
            'password': 'password123'
        }, follow_redirects=True)

    def login_restaurant_owner(self):
        """Helper method to log in as restaurant owner."""
        return self.app.post('/login', data={
            'username': 'test_owner',
            'password': 'password123'
        }, follow_redirects=True)

    def test_1_home_page_loads(self):
        """Test 1: Home page loads successfully."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'JustEat', response.data)

    def test_2_customer_login(self):
        """Test 2: Customer can log in successfully."""
        response = self.login_customer()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)

    def test_3_restaurant_owner_login(self):
        """Test 3: Restaurant owner can log in successfully."""
        response = self.login_restaurant_owner()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Restaurant Dashboard', response.data)

    def test_4_invalid_login(self):
        """Test 4: Invalid login credentials are rejected."""
        response = self.app.post('/login', data={
            'username': 'invalid_user',
            'password': 'wrong_password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_5_customer_browse_restaurants(self):
        """Test 5: Customer can browse restaurants."""
        self.login_customer()
        response = self.app.get('/customer/restaurants')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Restaurant', response.data)

    def test_6_customer_view_restaurant_menu(self):
        """Test 6: Customer can view restaurant menu."""
        self.login_customer()
        response = self.app.get(f'/customer/restaurant/{self.restaurant.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Pizza', response.data)

    def test_7_add_item_to_cart(self):
        """Test 7: Customer can add items to cart."""
        self.login_customer()
        response = self.app.post('/customer/add-to-cart',
            data=json.dumps({
                'menu_item_id': self.menu_item.id,
                'quantity': 2
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_8_view_cart(self):
        """Test 8: Customer can view cart."""
        self.login_customer()
        
        # Add item to cart first
        cart_item = Cart(
            customer_id=self.customer.id,
            menu_item_id=self.menu_item.id,
            quantity=1
        )
        db.session.add(cart_item)
        db.session.commit()
        
        response = self.app.get('/customer/cart')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Pizza', response.data)

    def test_9_place_order(self):
        """Test 9: Customer can place an order."""
        self.login_customer()
        
        # Add item to cart first
        cart_item = Cart(
            customer_id=self.customer.id,
            menu_item_id=self.menu_item.id,
            quantity=2
        )
        db.session.add(cart_item)
        db.session.commit()
        
        response = self.app.post('/customer/place-order',
            data=json.dumps({
                'restaurant_id': self.restaurant.id,
                'notes': 'Test order'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_10_restaurant_owner_dashboard(self):
        """Test 10: Restaurant owner can access dashboard."""
        self.login_restaurant_owner()
        response = self.app.get('/restaurant/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Restaurant Dashboard', response.data)

    def test_11_restaurant_owner_view_orders(self):
        """Test 11: Restaurant owner can view orders."""
        self.login_restaurant_owner()
        
        # Create a test order
        order = Order(
            customer_id=self.customer.id,
            restaurant_id=self.restaurant.id,
            total_amount=25.98,
            delivery_fee=2.99,
            tax_amount=2.08
        )
        db.session.add(order)
        db.session.commit()
        
        response = self.app.get('/restaurant/orders')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Orders Management', response.data)

    def test_12_update_order_status(self):
        """Test 12: Restaurant owner can update order status."""
        self.login_restaurant_owner()
        
        # Create a test order
        order = Order(
            customer_id=self.customer.id,
            restaurant_id=self.restaurant.id,
            total_amount=25.98,
            delivery_fee=2.99,
            tax_amount=2.08,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        
        response = self.app.post('/api/orders/update-status',
            data=json.dumps({
                'order_id': order.id,
                'status': 'confirmed'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_13_add_menu_item(self):
        """Test 13: Restaurant owner can add menu items."""
        self.login_restaurant_owner()
        
        response = self.app.post('/api/menu/add',
            data=json.dumps({
                'restaurant_id': self.restaurant.id,
                'name': 'New Pizza',
                'description': 'A new delicious pizza',
                'price': 15.99,
                'category': 'Pizza',
                'is_vegetarian': False
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_14_submit_review(self):
        """Test 14: Customer can submit restaurant reviews."""
        self.login_customer()
        
        response = self.app.post('/api/reviews',
            data=json.dumps({
                'restaurant_id': self.restaurant.id,
                'rating': 5,
                'comment': 'Excellent food!'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_15_toggle_favorite(self):
        """Test 15: Customer can toggle restaurant favorites."""
        self.login_customer()
        
        response = self.app.post('/api/favorites/toggle',
            data=json.dumps({
                'restaurant_id': self.restaurant.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_16_role_based_access_control(self):
        """Test 16: Role-based access control works correctly."""
        # Customer should not access restaurant dashboard
        self.login_customer()
        response = self.app.get('/restaurant/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Restaurant owner should not access customer cart
        self.login_restaurant_owner()
        response = self.app.get('/customer/cart')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_17_search_restaurants(self):
        """Test 17: Restaurant search functionality works."""
        self.login_customer()
        response = self.app.get('/customer/restaurants?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Restaurant', response.data)

    def test_18_filter_restaurants_by_cuisine(self):
        """Test 18: Restaurant filtering by cuisine works."""
        self.login_customer()
        response = self.app.get('/customer/restaurants?cuisine=Italian')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Restaurant', response.data)

    def test_19_order_history(self):
        """Test 19: Customer can view order history."""
        self.login_customer()
        
        # Create a test order
        order = Order(
            customer_id=self.customer.id,
            restaurant_id=self.restaurant.id,
            total_amount=25.98,
            delivery_fee=2.99,
            tax_amount=2.08
        )
        db.session.add(order)
        db.session.commit()
        
        response = self.app.get('/customer/orders')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Order History', response.data)

    def test_20_menu_item_availability(self):
        """Test 20: Menu item availability toggle works."""
        self.login_restaurant_owner()
        
        response = self.app.post('/api/menu/update',
            data=json.dumps({
                'item_id': self.menu_item.id,
                'is_available': False
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

if __name__ == '__main__':
    unittest.main()
