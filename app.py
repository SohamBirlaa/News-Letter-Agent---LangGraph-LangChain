from flask import Flask, request, jsonify, render_template, session
from agent import start_newsletter_agent, resume_newsletter_agent
from database import init_db, save_newsletter, get_all_newsletters, get_newsletter as get_newsletter_by_id
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session

# Initialize DB on app start
init_db()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# STEP 1 — Run agent (PAUSE for human review)
@app.route("/run-agent", methods=["POST"])
def run_agent():
    data = request.json
    goal = data.get("goal")

    if not goal:
        return jsonify({"error": "Goal is required"}), 400

    result = start_newsletter_agent(goal)

    # Store thread_id and goal in session so /approve can resume the same thread
    session["thread_id"] = result["thread_id"]
    session["goal"] = goal

    return jsonify({
        "status": "PAUSED_FOR_HUMAN_REVIEW",
        "draft_newsletter": result.get("newsletter", "No draft generated")
    })


# STEP 2 — Human approval → resume the SAME thread + save to DB
@app.route("/approve", methods=["POST"])
def approve():
    thread_id = session.get("thread_id")
    goal = session.get("goal")

    if not thread_id:
        return jsonify({"error": "No active session. Please run the agent first."}), 400

    result = resume_newsletter_agent(thread_id)

    final_newsletter = result.get("newsletter", "No newsletter generated")

    # Save to database
    save_newsletter(goal, final_newsletter)

    # Clear session after done
    session.pop("thread_id", None)
    session.pop("goal", None)

    return jsonify({
        "status": "NEWSLETTER_SENT",
        "newsletter": final_newsletter
    })


# STEP 3 — Read latest newsletter.md file
@app.route("/get-newsletter-file", methods=["GET"])
def get_newsletter_file():
    try:
        with open("newsletter.md", "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"file": content})
    except:
        return jsonify({"file": "Newsletter file not created yet."})


# STEP 4 — Get newsletter history list
@app.route("/history", methods=["GET"])
def history():
    rows = get_all_newsletters()
    return jsonify(rows)


# STEP 5 — Open single newsletter from history
@app.route("/newsletter/<int:nid>", methods=["GET"])
def open_newsletter(nid):
    content = get_newsletter_by_id(nid)
    return jsonify({"content": content})


if __name__ == "__main__":
    app.run(debug=True, port=5000)