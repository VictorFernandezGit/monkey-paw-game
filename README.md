# Monkey's Paw Game

A Flask web application where users make wishes that get twisted by an AI-powered Monkey's Paw.

## Redis Integration

This application uses **Redis** for:
- **Rate Limiting** (via Flask-Limiter)
- **Leaderboard Caching** (to reduce database load and speed up leaderboard queries)

### How Redis is Used
- **Rate Limiting:** Stores counters and metadata for each user/IP. Enforced globally and persists across restarts.
- **Leaderboard Caching:** The `/leaderboard` endpoint caches the top 10 users in Redis for 60 seconds. This reduces database queries and improves performance.

### Environment Variable
Set the following in your `.env` file:
```
REDIS_URL=redis://localhost:6379/0  # For local development
# or for Upstash/production:
# REDIS_URL=rediss://default:<your-token>@your-upstash-endpoint:6379
```

### Local Redis Setup (with Docker)
To run Redis locally for development:
```bash
docker run -d -p 6379:6379 --name monkeypaw-redis redis:7
```

### Production
- Use a managed Redis service (e.g., Upstash, Redis Cloud)
- Set `REDIS_URL` to your production Redis instance (use `rediss://` for SSL/TLS)

## Username & Game Flow
- The root page (`/`) is the username entry page. Users must enter a username to play.
- After entering a username, users are redirected to `/game` where the main game and leaderboard are shown.
- Sessions are managed securely with CSRF protection enabled.

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (create a `.env` file):
   ```
   FLASK_SECRET_KEY=your_secret_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=postgresql://localhost:5432/monkeypaw
   REDIS_URL=redis://localhost:6379/0
   ```

3. Create the database:
   ```bash
   createdb monkeypaw
   python init_db.py
   ```

4. Run the application:
   ```bash
   python app.py
   ```

## Production Deployment on Render

### Prerequisites
- Render account
- OpenAI API key
- Managed Redis (e.g., Upstash)

### Deployment Steps

1. **Push your code to GitHub**

2. **Create a new Web Service on Render:**
   - Connect your GitHub repository
   - Choose "Python" as the environment
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `gunicorn app:app`

3. **Configure Environment Variables:**
   - `FLASK_ENV`: `production`
   - `FLASK_SECRET_KEY`: Generate a secure random key
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `REDIS_URL`: Your Upstash or production Redis URL (e.g., `rediss://default:<token>@...`)

4. **Create a PostgreSQL Database:**
   - Create a new PostgreSQL database on Render
   - The `DATABASE_URL` will be automatically provided

5. **Initialize the Database:**
   - After deployment, run the database initialization:
   ```bash
   python init_db.py
   ```

### Important Notes

- The app automatically handles Render's PostgreSQL URL format
- Database tables are created automatically in development
- In production, run `init_db.py` once after deployment
- Make sure your OpenAI API key has sufficient credits
- The app runs on port 5001 locally to avoid AirPlay conflicts on macOS
- **Leaderboard is cached in Redis for 60 seconds** for performance

## Features

- User registration and session management
- AI-powered wish twisting using OpenAI GPT-4
- Streak tracking and leaderboard (with Redis caching)
- Game over after 5 failed wishes
- High score tracking
- Secure sessions and CSRF protection
