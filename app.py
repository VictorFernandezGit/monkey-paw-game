from flask import Flask, render_template, request, jsonify, session
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Monkey's Paw Persona Prompt
PAW_PROMPT = """
You are a cursed Monkey's Paw. Every wish must be granted literally, but with a cruel or ironic twist. 
Try to creatively subvert the user's intention in a clever and surprising way, unless the wish is so precisely worded that no twist can ruin it. 
After granting the wish, explain the twist.
"""

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/wish", methods=["POST"])
def wish():
    data = request.get_json()
    user_wish = data.get("wish", "")

    # Initialize streak and failed_wishes if not present
    if "streak" not in session:
        session["streak"] = 0
    if "failed_wishes" not in session:
        session["failed_wishes"] = 0

    system_prompt = PAW_PROMPT + "\n\nAfter the twist, evaluate if the user avoided the twist entirely. Answer YES or NO."

    user_input = f"""
I wish: {user_wish}

1. Twist the wish as the Monkey's Paw would.
2. Then answer ONLY with 'Did the user avoid a harmful twist? YES or NO' on the next line.
"""

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
        if "YES" in content.upper():
            result = "win"
            session["streak"] += 1
            session["failed_wishes"] = 0
        else:
            result = "lose"
            session["streak"] = 0
            session["failed_wishes"] += 1
        streak = session["streak"]
        failed_wishes = session["failed_wishes"]
        game_over = False
        if failed_wishes >= 5:
            game_over = True
            session["streak"] = 0
            session["failed_wishes"] = 0
        return jsonify({
            "twist": content,
            "result": result,
            "streak": streak,
            "failed_wishes": failed_wishes,
            "game_over": game_over
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)
