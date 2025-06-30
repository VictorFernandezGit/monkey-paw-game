# Monkey's Paw Game

A Flask web application where users make wishes that get twisted by an AI-powered Monkey's Paw.

## Redis for Rate Limiting

This application uses **Redis** as a backend for rate limiting via Flask-Limiter. Redis ensures that:
- Rate limits persist across app restarts and multiple server instances (distributed/scalable)
- Limits are enforced globally, not just per server
- The app is protected from abuse and denial-of-service attacks

### How Redis is Used
- **Purpose:** Stores rate limit counters and metadata for each user/IP
- **Integration:** Configured via the `REDIS_URL` environment variable
- **Fallback:** If Redis is not available, the app uses in-memory storage (not recommended for production)

### Local Redis Setup (with Docker)
To run Redis locally for development:
```bash
docker run -d -p 6379:6379 --name monkeypaw-redis redis:7
```

### Environment Variable
Add this to your `.env` file:
```
REDIS_URL=redis://localhost:6379
```

### Production
- Use a managed Redis service or your own Redis server
- Set `REDIS_URL` to your production Redis instance

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
   REDIS_URL=redis://localhost:6379
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

## Features

- User registration and session management
- AI-powered wish twisting using OpenAI GPT-4
- Streak tracking and leaderboard
- Game over after 5 failed wishes
- High score tracking 