#!/usr/bin/env python3
"""
Database Migration Script for FoodApp
Adds new columns to existing database tables
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add new columns to existing database tables"""
    
    # Database file path
    db_path = 'instance/justeat.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database with updated schema.")
        return create_new_database()
    
    print(f"Starting migration at {datetime.now()}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns in user table
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"Existing user columns: {existing_columns}")
        
        # Add new columns to user table if they don't exist
        new_user_columns = [
            ('latitude', 'FLOAT'),
            ('longitude', 'FLOAT'), 
            ('preferred_diet', 'VARCHAR(20) DEFAULT "all"')
        ]
        
        for column_name, column_type in new_user_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}")
                    print(f"Added column '{column_name}' to user table")
                except sqlite3.OperationalError as e:
                    print(f"Error adding column '{column_name}': {e}")
        
        # Check existing columns in restaurant table
        cursor.execute("PRAGMA table_info(restaurant)")
        existing_restaurant_columns = [column[1] for column in cursor.fetchall()]
        print(f"Existing restaurant columns: {existing_restaurant_columns}")
        
        # Add new columns to restaurant table if they don't exist
        new_restaurant_columns = [
            ('latitude', 'FLOAT'),
            ('longitude', 'FLOAT')
        ]
        
        for column_name, column_type in new_restaurant_columns:
            if column_name not in existing_restaurant_columns:
                try:
                    cursor.execute(f"ALTER TABLE restaurant ADD COLUMN {column_name} {column_type}")
                    print(f"Added column '{column_name}' to restaurant table")
                except sqlite3.OperationalError as e:
                    print(f"Error adding column '{column_name}': {e}")
        
        # Check existing columns in menu_item table
        cursor.execute("PRAGMA table_info(menu_item)")
        existing_menu_columns = [column[1] for column in cursor.fetchall()]
        print(f"Existing menu_item columns: {existing_menu_columns}")
        
        # Add new columns to menu_item table if they don't exist
        new_menu_columns = [
            ('is_non_veg', 'BOOLEAN DEFAULT 0'),
            ('subcategory', 'VARCHAR(50)'),
            ('food_type', 'VARCHAR(50)')
        ]
        
        for column_name, column_type in new_menu_columns:
            if column_name not in existing_menu_columns:
                try:
                    cursor.execute(f"ALTER TABLE menu_item ADD COLUMN {column_name} {column_type}")
                    print(f"Added column '{column_name}' to menu_item table")
                except sqlite3.OperationalError as e:
                    print(f"Error adding column '{column_name}': {e}")
        
        # Check existing columns in review table
        cursor.execute("PRAGMA table_info(review)")
        existing_review_columns = [column[1] for column in cursor.fetchall()]
        print(f"Existing review columns: {existing_review_columns}")
        
        # Add new column to review table if it doesn't exist
        if 'order_id' not in existing_review_columns:
            try:
                cursor.execute("ALTER TABLE review ADD COLUMN order_id INTEGER")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_review_order_id ON review (order_id)")
                print("Added column 'order_id' to review table")
            except sqlite3.OperationalError as e:
                print(f"Error adding column 'order_id': {e}")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Show updated table schemas
        print("\nUpdated table schemas:")
        for table in ['user', 'restaurant', 'menu_item', 'review']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n{table} table columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def create_new_database():
    """Create new database with updated schema"""
    print("Creating new database with updated schema...")
    
    # Import and initialize the Flask app to create tables
    try:
        import sys
        sys.path.append('.')
        
        # Import the Flask app factory
        from app import create_app
        from models import db
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("New database created successfully!")
            return True
    except Exception as e:
        print(f"Error creating new database: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\nDatabase migration completed successfully!")
        print("You can now run your Flask application.")
    else:
        print("\nDatabase migration failed!")
        print("Please check the error messages above.")
