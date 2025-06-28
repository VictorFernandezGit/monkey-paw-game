# Database Migrations

This directory contains database migration scripts for the Monkey's Paw application.

## How to Run Migrations

1. **Ensure your virtual environment is activated:**
   ```bash
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

2. **Run a specific migration:**
   ```bash
   python migrations/YYYYMMDD_description.py
   ```

## Migration History

- **20240610_add_avoided_twists.py** - Added `avoided_twists` column to users table

## Best Practices

- Always backup your database before running migrations
- Test migrations on a copy of your production data first
- Run migrations in chronological order
- Document any manual steps required in the migration script comments

## Creating New Migrations

When you need to make database schema changes:

1. Create a new file with the format: `YYYYMMDD_description.py`
2. Use the existing migration scripts as templates
3. Test the migration thoroughly
4. Update this README with the new migration entry 