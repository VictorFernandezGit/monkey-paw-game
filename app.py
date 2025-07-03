import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import openai
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import random
import re
import bleach
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import secrets
import redis
from datetime import datetime

load_dotenv()


app = Flask(__name__)

# Security Configuration
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout
app.config['SESSION_COOKIE_SECURE'] = False  # Force to False for local development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize security extensions
csrf = CSRFProtect(app)

# Configure rate limiter storage
if os.getenv('FLASK_ENV') == 'production':
    try:
        from flask_limiter.util import get_remote_address
        from flask_limiter import Limiter
        import redis

        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        print("DEBUG: Attempting to use Redis at", redis_url)
        # Try a direct connection test
        try:
            r = redis.Redis.from_url(redis_url)
            r.ping()
            print("DEBUG: Successfully connected to Redis!")
        except Exception as conn_err:
            print("ERROR: Could not connect to Redis:", conn_err)

        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=redis_url,
            default_limits=["200 per day", "50 per hour"]
        )
        print("✅ Rate limiter configured with Redis storage")
    except ImportError as e:
        print("⚠️ Redis not available (ImportError):", e)
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
    except Exception as e:
        print("⚠️ Redis not available (Other Exception):", e)
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
else:
    # Use memory storage for development (with warning suppression)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
    print("ℹ️ Rate limiter using memory storage (development mode)")

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Warning: OPENAI_API_KEY not set. The wish functionality will not work.")

# Database setup
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'postgresql://localhost:5432/monkeypaw'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Input validation functions
def validate_username(username):
    """Validate and sanitize username input"""
    if not username or len(username.strip()) == 0:
        return None, "Username cannot be empty"
    
    username = username.strip()
    
    # Length validation
    if len(username) < 2 or len(username) > 50:
        return None, "Username must be between 2 and 50 characters"
    
    # Character validation - only allow alphanumeric, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return None, "Username can only contain letters, numbers, hyphens, and underscores"
    
    # Sanitize to prevent XSS
    username = bleach.clean(username, tags=[], strip=True)
    
    return username, None

def validate_wish(wish):
    """Validate and sanitize wish input"""
    if not wish or len(wish.strip()) == 0:
        return None, "Wish cannot be empty"
    
    wish = wish.strip()
    
    # Length validation
    if len(wish) < 5 or len(wish) > 500:
        return None, "Wish must be between 5 and 500 characters"
    
    # Check for potentially malicious content
    dangerous_patterns = [
        r'<script', r'javascript:', r'data:', r'vbscript:', r'on\w+\s*=',
        r'<iframe', r'<object', r'<embed', r'<form', r'<input'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, wish, re.IGNORECASE):
            return None, "Wish contains potentially unsafe content"
    
    # Sanitize to prevent XSS while preserving basic formatting
    allowed_tags = ['b', 'i', 'em', 'strong']
    wish = bleach.clean(wish, tags=allowed_tags, strip=True)
    
    return wish, None

# Only create tables in development
if os.getenv('FLASK_ENV') != 'production':
    with app.app_context():
        db.create_all()
else:
    # In production, try to create tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created/verified successfully!")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
            # Continue running even if tables already exist

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    streak = db.Column(db.Integer, default=0)
    wishes_made = db.Column(db.Integer, default=0)
    failed_wishes = db.Column(db.Integer, default=0)
    high_score = db.Column(db.Integer, default=0)
    avoided_twists = db.Column(db.Integer, default=0)
    spellbook_uses = db.Column(db.Integer, default=0)
    session_number = db.Column(db.Integer, default=1)  # Track game sessions

    def to_dict(self):
        return {
            'username': self.username,
            'streak': self.streak,
            'wishes_made': self.wishes_made,
            'failed_wishes': self.failed_wishes,
            'high_score': self.high_score,
            'avoided_twists': self.avoided_twists,
            'spellbook_uses': self.spellbook_uses,
            'session_number': self.session_number
        }

class WishHistory(db.Model):
    __tablename__ = 'wish_history'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('users.username'), nullable=False)
    wish_text = db.Column(db.Text, nullable=False)
    twist_result = db.Column(db.Text, nullable=False)
    outcome = db.Column(db.String(10), nullable=False)  # 'win' or 'lose'
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    user_agent = db.Column(db.Text, nullable=True)
    wish_quality_bonus = db.Column(db.Float, nullable=True)
    positive_indicator_count = db.Column(db.Integer, nullable=True)
    negative_indicator_count = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_number = db.Column(db.Integer, nullable=False, default=1)  # Game session

# Monkey's Paw Persona Prompt
PAW_PROMPT = """
You are a cursed Monkey's Paw. You must grant every wish with an ironic or cruel twist.

After granting the wish, evaluate:
1. Was the original intent of the wish completely subverted by the twist?
2. Would a reasonable person be satisfied with the outcome?

If both answers are YES, the user **loses**.
If either is NO, the user **wins**.

However, be slightly more lenient than before. A well-crafted wish with good intentions should have a reasonable chance of success.

Respond with:
- The twisted wish result
- Final line: \"User outcome: WIN\" or \"User outcome: LOSE\"
"""

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("game"))
    return render_template("username.html")

@app.route("/game")
def game():
    if "username" not in session:
        return redirect(url_for("index"))
    return render_template("index.html")

@app.route("/username")
def username():
    return render_template("username.html")

@app.route("/set_username", methods=["POST"])
@limiter.limit("10 per minute")
def set_username():
    if request.is_json:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        username = data.get("username", "")
        validated_username, error = validate_username(username)
        if error:
            return jsonify({"error": error}), 400
        user = User.query.filter_by(username=validated_username).first()
        if not user:
            user = User(username=validated_username)
            db.session.add(user)
            db.session.commit()
        session["username"] = validated_username
        session.permanent = True
        return jsonify({"success": True, "username": validated_username})
    else:
        username = request.form.get("username", "")
        validated_username, error = validate_username(username)
        if error:
            # Optionally flash error here
            return redirect(url_for("index"))
        user = User.query.filter_by(username=validated_username).first()
        if not user:
            user = User(username=validated_username)
            db.session.add(user)
            db.session.commit()
        session["username"] = validated_username
        session.permanent = True
        return redirect(url_for("game"))

@app.route("/leaderboard", methods=["GET"])
@limiter.limit("30 per minute")
def leaderboard():
    try:
        users = User.query.order_by(User.high_score.desc()).limit(10).all()
        # Return username, high_score, avoided_twists (from last game), and current streak
        sorted_lb = [(u.username, u.high_score, u.avoided_twists, u.streak) for u in users]
        return jsonify(sorted_lb)
    except Exception as e:
        print("Leaderboard error:", e)
        return jsonify({"error": "Could not load leaderboard"}), 500

@app.route("/wish", methods=["POST"])
@limiter.limit("20 per minute")
def wish():
    try:
        if "username" not in session:
            return jsonify({"error": "No username set. Please enter your username to start."}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        user_wish = data.get("wish", "")
        validated_wish, error = validate_wish(user_wish)
        
        if error:
            return jsonify({"error": error}), 400
            
        username = session["username"]
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        user.wishes_made += 1

        system_prompt = PAW_PROMPT
        user_input = f"I wish: {validated_wish}\n\nTwist the wish as the Monkey's Paw would. Then, on the final line, write 'User outcome: WIN' or 'User outcome: LOSE' as described."

        try:
            client = OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            content = response.choices[0].message.content
            
            # Sanitize the response content
            content = bleach.clean(content, tags=[], strip=True)
            
            # Parse the outcome from the final line
            outcome = "lose"
            if "user outcome: win" in content.lower():
                outcome = "win"
            elif "user outcome: lose" in content.lower():
                outcome = "lose"
            
            # Apply probability-based system to give players a chance
            # Base win probability (30% chance to win regardless of AI interpretation)
            base_win_chance = 0.30
            
            # Bonus for well-crafted wishes (wishes that are specific, positive, and modest)
            wish_quality_bonus = 0.0
            wish_lower = validated_wish.lower()
            
            # Positive indicators that increase win chance
            positive_indicators = [
                'wisdom', 'strength', 'courage', 'patience', 'gratitude', 'help', 'learn', 'grow',
                'small', 'little', 'moment', 'today', 'today', 'week', 'day', 'hour', 'minute',
                'genuine', 'sincere', 'humble', 'modest', 'simple', 'peaceful', 'kind', 'good'
            ]
            
            # Negative indicators that decrease win chance
            negative_indicators = [
                'infinite', 'eternal', 'forever', 'never', 'all', 'every', 'everything', 'unlimited',
                'power', 'control', 'wealth', 'money', 'rich', 'famous', 'immortal', 'perfect',
                'world', 'universe', 'destroy', 'kill', 'death', 'evil', 'curse', 'hate'
            ]
            
            # Calculate wish quality bonus
            positive_count = sum(1 for word in positive_indicators if word in wish_lower)
            negative_count = sum(1 for word in negative_indicators if word in wish_lower)
            
            wish_quality_bonus = (positive_count * 0.05) - (negative_count * 0.10)
            wish_quality_bonus = max(-0.20, min(0.30, wish_quality_bonus))  # Clamp between -20% and +30%
            
            # Calculate final win probability
            final_win_chance = base_win_chance + wish_quality_bonus
            final_win_chance = max(0.10, min(0.70, final_win_chance))  # Clamp between 10% and 70%
            
            # Determine final outcome based on probability
            if random.random() < final_win_chance:
                result = "win"
                # Update the content to reflect the win
                content = content.replace("User outcome: LOSE", "User outcome: WIN")
                if "User outcome: lose" in content:
                    content = content.replace("User outcome: lose", "User outcome: WIN")
            else:
                result = "lose"
                # Update the content to reflect the loss
                content = content.replace("User outcome: WIN", "User outcome: LOSE")
                if "User outcome: win" in content:
                    content = content.replace("User outcome: win", "User outcome: LOSE")
            
            print(f"Wish: {validated_wish}")
            print(f"Positive indicators: {positive_count}, Negative indicators: {negative_count}")
            print(f"Wish quality bonus: {wish_quality_bonus:.2f}")
            print(f"Final win chance: {final_win_chance:.2f}")
            print(f"Random roll: {random.random():.2f}")
            print(f"Final result: {result}")
            
            # Store wish history in the database
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            user_agent = request.headers.get('User-Agent')
            wish_history = WishHistory(
                username=username,
                wish_text=validated_wish,
                twist_result=content,
                outcome=result,
                ip_address=ip_address,
                user_agent=user_agent,
                wish_quality_bonus=wish_quality_bonus,
                positive_indicator_count=positive_count,
                negative_indicator_count=negative_count,
                session_number=user.session_number
            )
            db.session.add(wish_history)
            
            # Update streak and failed_wishes based on result
            if result == "win":
                user.streak += 1
                user.failed_wishes = 0
            else:
                user.streak = 0
                user.failed_wishes += 1
            streak = user.streak
            failed_wishes = user.failed_wishes
            wishes_made = user.wishes_made
            game_over = False
            if failed_wishes >= 5:
                game_over = True
                if streak > user.high_score:
                    user.high_score = streak
                # At game over, count avoided_twists from WishHistory for this session
                avoided_twists = WishHistory.query.filter_by(
                    username=username,
                    outcome='win',
                    session_number=user.session_number
                ).count()
                user.avoided_twists = avoided_twists
                # Increment session_number for next game
                user.session_number += 1
                user.streak = 0
                user.failed_wishes = 0
                user.wishes_made = 0
                user.spellbook_uses = 0
            else:
                # For in-game display, count so far in this session
                avoided_twists = WishHistory.query.filter_by(
                    username=username,
                    outcome='win',
                    session_number=user.session_number
                ).count()
                user.avoided_twists = avoided_twists
            db.session.commit()
            return jsonify({
                "twist": content,
                "result": result,
                "streak": streak,
                "failed_wishes": failed_wishes,
                "game_over": game_over,
                "wishes_made": wishes_made,
                "avoided_twists": avoided_twists,
                "spellbook_uses": user.spellbook_uses,
                "username": user.username
            })
        except Exception as e:
            print("OpenAI API error:", e)
            return jsonify({"error": "Service temporarily unavailable"}), 500
    except Exception as e:
        print("Wish endpoint error:", e)
        return jsonify({"error": "An error occurred while processing your wish"}), 500

@app.route("/generate_suggestions", methods=["POST"])
@limiter.limit("5 per minute")
def generate_suggestions():
    try:
        if "username" not in session:
            return jsonify({"error": "No username set. Please enter your username to start."}), 401
            
        username = session["username"]
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        # Check if user has exceeded spellbook uses (3 per game)
        if user.spellbook_uses >= 3:
            return jsonify({"error": "You have used all 3 spellbook charges for this game."}), 403

        # Check if game is over (5 failed wishes)
        if user.failed_wishes >= 5:
            return jsonify({"error": "Game over! You cannot use the spellbook after losing."}), 403

        if not openai_api_key:
            return jsonify({"error": "Service temporarily unavailable"}), 500
            
        client = OpenAI(api_key=openai_api_key)
        
        # Prompt designed to generate wishes that are harder for the monkey's paw to twist
        suggestion_prompt = """
        You are an ancient spellbook that helps people craft wishes to avoid the Monkey's Paw's curse.
        
        Generate 3 wish suggestions that are strategically designed to be difficult for the Monkey's Paw to twist negatively.
        
        Rules for good wishes:
        1. Be specific and detailed to avoid ambiguity
        2. Include positive conditions and safeguards
        3. Focus on personal growth, wisdom, or helping others
        4. Avoid material wealth, power, or immortality
        5. Use precise language that leaves little room for interpretation
        6. Include time limits or specific contexts when possible
        7. Emphasize the journey/process rather than just the outcome
        
        Format each suggestion as a complete wish starting with "I wish..."
        Make each wish unique and creative.
        
        Return only the 3 wishes, one per line, no numbering or extra text.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": suggestion_prompt}
            ],
            max_tokens=200,
            temperature=0.8
        )
        
        suggestions = response.choices[0].message.content.strip().split('\n')
        # Clean up suggestions and ensure we have exactly 3
        suggestions = [s.strip() for s in suggestions if s.strip() and s.strip().startswith('I wish')][:3]
        
        # Sanitize suggestions
        suggestions = [bleach.clean(s, tags=[], strip=True) for s in suggestions]
        
        # If we don't have 3 suggestions, add some fallbacks
        while len(suggestions) < 3:
            fallbacks = [
                "I wish for the wisdom to make the best decisions in the next 24 hours",
                "I wish for the strength to help someone in need today",
                "I wish for a moment of genuine gratitude for what I already have"
            ]
            suggestions.append(fallbacks[len(suggestions) - len(suggestions)])
        
        # Increment spellbook uses
        user.spellbook_uses += 1
        db.session.commit()
        
        return jsonify({
            "suggestions": suggestions,
            "spellbook_uses": user.spellbook_uses,
            "remaining_uses": 3 - user.spellbook_uses
        })
        
    except Exception as e:
        print("Suggestion generation error:", e)
        return jsonify({"error": "Could not generate suggestions at this time"}), 500
    


if __name__ == "__main__":
    app.run(debug=True)
