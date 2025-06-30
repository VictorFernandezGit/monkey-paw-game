#!/usr/bin/env python3
"""
Database reset script for Monkey's Paw application.
WARNING: This will delete ALL data and recreate tables from scratch.
"""

import os
from app import app, db

def reset_database():
    with app.app_context():
        try:
            print("🗑️ Dropping all existing tables...")
            db.drop_all()
            print("✅ All tables dropped successfully!")
            
            print("🏗️ Creating new tables with updated schema...")
            db.create_all()
            print("✅ New tables created successfully!")
            
            # Verify tables exist
            from app import User
            user_count = User.query.count()
            print(f"✅ Database reset complete. Current user count: {user_count}")
            print("🎉 Database is now fresh and ready for new games!")
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            raise

if __name__ == "__main__":
    print("⚠️ WARNING: This will delete ALL existing data!")
    print("Are you sure you want to reset the database? (y/N): ", end="")
    
    response = input().strip().lower()
    if response in ['y', 'yes']:
        reset_database()
    else:
        print("❌ Database reset cancelled.") 