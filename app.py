from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime
import os

app = Flask(__name__, static_folder=".")

messages = []
reactions = {"heart": 0, "clap": 0, "party": 0}


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/messages", methods=["GET"])
def get_messages():
    return jsonify(messages)


@app.route("/messages", methods=["POST"])
def post_message():
    data = request.get_json()
    name = (data.get("name") or "名無し")[:20]
    text = (data.get("text") or "")[:200]
    if not text.strip():
        return jsonify({"error": "text is required"}), 400
    msg = {
        "name": name,
        "text": text,
        "time": datetime.now().strftime("%H:%M"),
    }
    messages.insert(0, msg)
    if len(messages) > 100:
        messages.pop()
    return jsonify(msg), 201


@app.route("/reactions", methods=["GET"])
def get_reactions():
    return jsonify(reactions)


@app.route("/reactions/<reaction_type>", methods=["POST"])
def post_reaction(reaction_type):
    if reaction_type not in reactions:
        return jsonify({"error": "unknown reaction"}), 400
    reactions[reaction_type] += 1
    return jsonify(reactions)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
