#!/usr/bin/env python3
"""
Database initialization script for production deployment.
Run this script once after deploying to create the database tables.
"""

import os
from app import app, db

def init_database():
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Verify tables exist
            from app import User
            user_count = User.query.count()
            print(f"✅ Database is ready. Current user count: {user_count}")
            
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            raise

if __name__ == "__main__":
    init_database() 