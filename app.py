from flask import Flask
from flask_login import LoginManager
import logging
import os

# Initialize extensions
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///justeat.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Import and initialize db from models
    from models import db
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Import routes
    from routes import register_routes, register_restaurant_routes
    register_routes(app)              # customer + auth routes
    register_restaurant_routes(app)   # restaurant owner routes

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from models import db
        db.create_all()
    app.run(debug=True)
