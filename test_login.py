#!/usr/bin/env python3
"""
Quick test script to verify login functionality
"""

from app import create_app, db
from models import User
from werkzeug.security import check_password_hash

def test_login():
    """Test the login functionality with demo users"""
    app = create_app()
    
    with app.app_context():
        # Test if demo users exist and passwords work
        test_users = ['john_doe', 'jane_smith', 'pizza_palace_owner']
        
        for username in test_users:
            user = User.query.filter_by(username=username).first()
            if user:
                # Test password verification
                password_valid = check_password_hash(user.password_hash, 'password123')
                print(f"User: {username}")
                print(f"  - Found in database: YES")
                print(f"  - Password valid: {'YES' if password_valid else 'NO'}")
                print(f"  - Role: {user.role}")
                print(f"  - Email: {user.email}")
                print()
            else:
                print(f"User {username}: NOT FOUND in database")
        
        # Count total users
        total_users = User.query.count()
        print(f"Total users in database: {total_users}")

if __name__ == '__main__':
    test_login()
