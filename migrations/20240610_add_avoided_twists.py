#!/usr/bin/env python3
"""
Database migration script to add avoided_twists column.
Run this script to update existing database schema.
"""

import os
import sys
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Create a minimal Flask app for the migration
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key_change_in_production")

# Database setup
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'postgresql://localhost:5432/monkeypaw'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def migrate_database():
    with app.app_context():
        try:
            # Add the avoided_twists column to existing users table
            with db.engine.connect() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avoided_twists INTEGER DEFAULT 0"))
                connection.commit()
            print("✅ Successfully added avoided_twists column to users table!")
            
            # Verify the column was added by checking table structure
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'avoided_twists'"))
                if result.fetchone():
                    print("✅ Column verification successful!")
                else:
                    print("⚠️ Column verification failed - column may not have been added")
            
        except Exception as e:
            print(f"❌ Error during database migration: {e}")
            raise

if __name__ == "__main__":
    migrate_database() 