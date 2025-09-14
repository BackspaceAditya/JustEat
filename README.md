# JustEat - Food Delivery Application

A comprehensive food delivery web application built with Flask, featuring UberEats-like UI and functionality for both customers and restaurant owners.

## Features

### Common Functionality
- **Role-based Authentication**: Customer and Restaurant Owner login with secure password management
- **Password Reset**: Email-based password reset functionality
- **Responsive Design**: Mobile-friendly UberEats-inspired interface
- **Toast Notifications**: Real-time feedback for all user actions

### Customer Features
- **Restaurant Discovery**: Browse and search restaurants by location, cuisine, or name
- **Advanced Filtering**: Filter by cuisine type, rating, delivery time, and price
- **Menu Browsing**: View detailed menus with prices, descriptions, and dietary information
- **Smart Cart**: Add items to cart with quantity selection and special instructions
- **Order Management**: Place orders with real-time status tracking
- **Order History**: View past orders with search functionality and reorder capability
- **Favorites**: Save favorite restaurants for quick access
- **Smart Recommendations**: Personalized food recommendations based on order history
- **Reviews & Ratings**: Rate and review restaurants and dishes

### Restaurant Owner Features
- **Restaurant Management**: Manage multiple restaurant profiles
- **Menu Management**: Add, edit, delete, and toggle availability of menu items
- **Order Processing**: View and update order status in real-time
- **Special Items**: Mark items as "Today's Special" or "Deal of the Day"
- **Analytics**: View order statistics and popular items
- **Automatic Tags**: Items ordered 10+ times per day get "Mostly Ordered" tag

### Technical Features
- **Database**: SQLite with SQLAlchemy ORM
- **Security**: Role-based access control and form validation
- **Logging**: Comprehensive application logging for debugging
- **Error Handling**: Robust error handling throughout the application
- **Unit Testing**: 20+ comprehensive unit tests covering all major functionality

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Templating**: Jinja2
- **Authentication**: Flask-Login
- **Styling**: Custom CSS with UberEats-inspired design

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone or Download
Download the project files to your local machine.

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

## Demo Accounts

The application comes with pre-seeded demo accounts for testing:

### Customer Accounts
- **Username**: `john_doe` | **Password**: `password123`
- **Username**: `jane_smith` | **Password**: `password123`

### Restaurant Owner Accounts
- **Username**: `pizza_palace_owner` | **Password**: `password123`
- **Username**: `burger_barn_owner` | **Password**: `password123`
- **Username**: `sushi_spot_owner` | **Password**: `password123`

## Project Structure

```
FoodApp Project/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── routes.py              # Application routes and API endpoints
├── requirements.txt       # Python dependencies
├── test_app.py           # Unit tests
├── README.md             # This file
├── static/
│   ├── css/
│   │   └── style.css     # Custom CSS styles
│   ├── js/
│   │   └── main.js       # JavaScript functionality
│   └── images/           # Static images
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── login.html        # Login page
    ├── reset_password.html
    ├── customer/         # Customer templates
    │   ├── dashboard.html
    │   ├── restaurants.html
    │   ├── restaurant_menu.html
    │   ├── cart.html
    │   ├── orders.html
    │   └── order_details.html
    └── restaurant/       # Restaurant owner templates
        ├── dashboard.html
        ├── orders.html
        └── menu_management.html
```

## Database Schema

### Core Models
- **User**: Customer and restaurant owner accounts
- **Restaurant**: Restaurant information and settings
- **MenuItem**: Menu items with categories and dietary information
- **Order**: Customer orders with status tracking
- **OrderItem**: Individual items within orders
- **Cart**: Shopping cart functionality
- **Review**: Customer reviews and ratings
- **Favorite**: Customer favorite restaurants

## API Endpoints

### Customer APIs
- `POST /customer/add-to-cart` - Add items to cart
- `GET /api/cart/count` - Get cart item count
- `POST /api/cart/update` - Update cart quantities
- `POST /api/cart/remove` - Remove items from cart
- `POST /customer/place-order` - Place new order
- `POST /api/favorites/toggle` - Toggle restaurant favorites
- `POST /api/reviews` - Submit restaurant reviews
- `POST /api/orders/reorder` - Reorder previous orders

### Restaurant Owner APIs
- `POST /api/orders/update-status` - Update order status
- `POST /api/menu/add` - Add new menu items
- `POST /api/menu/update` - Update existing menu items
- `POST /api/menu/delete` - Delete menu items

## Testing

Run the comprehensive test suite:

```bash
python -m unittest test_app.py -v
```

The test suite includes 20+ tests covering:
- Authentication and authorization
- Customer functionality (browsing, ordering, cart management)
- Restaurant owner functionality (menu and order management)
- API endpoints and data validation
- Role-based access control
- Search and filtering capabilities

## Key Features Implementation

### Smart Recommendations
The application provides personalized recommendations based on:
- Customer order history
- Preferred cuisine types
- Popular items in preferred categories
- Items not yet tried by the customer

### Order Status Tracking
Real-time order status updates with timeline:
1. **Pending** - Order placed, awaiting confirmation
2. **Confirmed** - Restaurant confirmed the order
3. **Preparing** - Food is being prepared
4. **Ready** - Order ready for pickup/delivery
5. **Delivered** - Order completed

### Responsive Design
- Mobile-first approach with responsive breakpoints
- Touch-friendly interface for mobile devices
- Optimized layouts for tablets and desktops
- UberEats-inspired color scheme and typography

## Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **Role-based Access**: Strict separation between customer and restaurant owner functions
- **Input Validation**: Server-side validation for all forms and API endpoints
- **CSRF Protection**: Cross-site request forgery protection
- **SQL Injection Prevention**: Parameterized queries through SQLAlchemy

## Performance Considerations

- **Database Indexing**: Optimized queries with proper indexing
- **Pagination**: Large datasets paginated for better performance
- **Caching**: Static asset caching for improved load times
- **Lazy Loading**: Efficient database relationship loading

## Future Enhancements

Potential improvements for production deployment:
- Payment gateway integration
- Real-time notifications using WebSockets
- Email notifications for order updates
- Image upload for restaurants and menu items
- Advanced analytics dashboard
- Multi-language support
- Delivery tracking with maps integration

## Troubleshooting

### Common Issues

1. **Database not found**: Run `python app.py` to create the database automatically
2. **Import errors**: Ensure all dependencies are installed via `pip install -r requirements.txt`
3. **Port already in use**: Change the port in `app.py` or stop other Flask applications

### Logging
Application logs are written to `app.log` for debugging purposes.

## Contributing

This is a demonstration project showcasing modern web development practices with Flask. The codebase follows:
- PEP 8 coding standards
- SOLID design principles
- Clean coding practices
- Comprehensive error handling
- Extensive testing coverage

## License

This project is created for educational and demonstration purposes.

---

**JustEat** - Bringing delicious food to your doorstep! 🍕🍔🍣
