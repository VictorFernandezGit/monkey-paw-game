import json
from flask import Flask, render_template, request, jsonify, session
import openai
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key_change_in_production")
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

# Only create tables in development
if os.getenv('FLASK_ENV') != 'production':
    with app.app_context():
        db.create_all()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    streak = db.Column(db.Integer, default=0)
    wishes_made = db.Column(db.Integer, default=0)
    failed_wishes = db.Column(db.Integer, default=0)
    high_score = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'username': self.username,
            'streak': self.streak,
            'wishes_made': self.wishes_made,
            'failed_wishes': self.failed_wishes,
            'high_score': self.high_score
        }

# Monkey's Paw Persona Prompt
PAW_PROMPT = """
You are a cursed Monkey's Paw. You must grant every wish with an ironic or cruel twist.

After granting the wish, evaluate:
1. Was the original intent of the wish completely subverted by the twist?
2. Would a reasonable person be satisfied with the outcome?

If both answers are YES, the user **loses**.
If either is NO, the user **wins**.

Respond with:
- The twisted wish result
- Final line: \"User outcome: WIN\" or \"User outcome: LOSE\"
"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/set_username", methods=["POST"])
def set_username():
    data = request.get_json()
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username required."}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    session["username"] = username
    return jsonify({"success": True, "username": username})

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    users = User.query.order_by(User.high_score.desc()).limit(10).all()
    sorted_lb = [(u.username, u.high_score) for u in users]
    return jsonify(sorted_lb)

@app.route("/wish", methods=["POST"])
def wish():
    try:
        if "username" not in session:
            return jsonify({"error": "No username set. Please enter your username to start."}), 401
        data = request.get_json()
        user_wish = data.get("wish", "")
        username = session["username"]
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        user.wishes_made += 1

        system_prompt = PAW_PROMPT
        user_input = f"I wish: {user_wish}\n\nTwist the wish as the Monkey's Paw would. Then, on the final line, write 'User outcome: WIN' or 'User outcome: LOSE' as described."

        try:
            client = openai.OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            content = response.choices[0].message.content
            # Parse the outcome from the final line
            outcome = "lose"
            if "user outcome: win" in content.lower():
                outcome = "win"
            elif "user outcome: lose" in content.lower():
                outcome = "lose"
            result = outcome
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
                user.streak = 0
                user.failed_wishes = 0
                user.wishes_made = 0
            db.session.commit()
            return jsonify({
                "twist": content,
                "result": result,
                "streak": streak,
                "failed_wishes": failed_wishes,
                "game_over": game_over,
                "wishes_made": wishes_made,
                "username": user.username
            })
        except Exception as e:
            print("OpenAI API error:", e)
            return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        print("Wish endpoint error:", e)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
