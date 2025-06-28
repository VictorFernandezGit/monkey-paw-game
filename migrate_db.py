#!/usr/bin/env python3
"""
Database migration script to add avoided_twists column.
Run this script to update existing database schema.
"""

import os
from app import app, db
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        try:
            # Add the avoided_twists column to existing users table
            with db.engine.connect() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avoided_twists INTEGER DEFAULT 0"))
                connection.commit()
            print("✅ Successfully added avoided_twists column to users table!")
            
            # Verify the column was added
            from app import User
            user_count = User.query.count()
            print(f"✅ Database migration complete. Current user count: {user_count}")
            
        except Exception as e:
            print(f"❌ Error during database migration: {e}")
            raise

if __name__ == "__main__":
    migrate_database() 