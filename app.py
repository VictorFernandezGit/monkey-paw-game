import json
from flask import Flask, render_template, request, jsonify, session
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")
openai.api_key = os.getenv("OPENAI_API_KEY")

LEADERBOARD_FILE = "leaderboard.json"

# Helper to load/save leaderboard

def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return {}
    with open(LEADERBOARD_FILE, "r") as f:
        return json.load(f)

def save_leaderboard(lb):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(lb, f)

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
    session["username"] = username
    # Optionally reset stats for new user
    session["streak"] = 0
    session["failed_wishes"] = 0
    session["wishes_made"] = 0
    return jsonify({"success": True, "username": username})

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    lb = load_leaderboard()
    # Return top 10 by streak
    sorted_lb = sorted(lb.items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify(sorted_lb)

@app.route("/wish", methods=["POST"])
def wish():
    if "username" not in session:
        return jsonify({"error": "No username set. Please enter your username to start."}), 401
    data = request.get_json()
    user_wish = data.get("wish", "")

    # Initialize streak, failed_wishes, and wishes_made if not present
    if "streak" not in session:
        session["streak"] = 0
    if "failed_wishes" not in session:
        session["failed_wishes"] = 0
    if "wishes_made" not in session:
        session["wishes_made"] = 0
    session["wishes_made"] += 1

    system_prompt = PAW_PROMPT

    user_input = f"I wish: {user_wish}\n\nTwist the wish as the Monkey's Paw would. Then, on the final line, write 'User outcome: WIN' or 'User outcome: LOSE' as described."

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
            session["streak"] += 1
            session["failed_wishes"] = 0
        else:
            session["streak"] = 0
            session["failed_wishes"] += 1
        streak = session["streak"]
        failed_wishes = session["failed_wishes"]
        wishes_made = session["wishes_made"]
        game_over = False
        if failed_wishes >= 5:
            game_over = True
            # Update leaderboard if new high streak
            lb = load_leaderboard()
            username = session["username"]
            if username:
                prev_best = lb.get(username, 0)
                if streak > prev_best:
                    lb[username] = streak
                    save_leaderboard(lb)
            session["streak"] = 0
            session["failed_wishes"] = 0
            session["wishes_made"] = 0
        return jsonify({
            "twist": content,
            "result": result,
            "streak": streak,
            "failed_wishes": failed_wishes,
            "game_over": game_over,
            "wishes_made": wishes_made,
            "username": session["username"]
        })
    except Exception as e:
        print("Wish error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
