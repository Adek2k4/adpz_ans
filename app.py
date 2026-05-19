from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
import re

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "submissions.json")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class Submission:
    name: str
    email: str
    message: str
    created_at: str

    def validate(self):
        errors = {}
        if not self.name.strip():
            errors["name"] = "Name is required."
        if not self.email.strip():
            errors["email"] = "Email is required."
        elif not EMAIL_RE.match(self.email):
            errors["email"] = "Email format is invalid."
        if not self.message.strip():
            errors["message"] = "Message is required."
        return errors


def load_submissions():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return []


def save_submissions(items):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2)


@app.route("/")
def index():
    return render_template("index.html", title="Home")


@app.route("/kontakt")
def kontakt():
    return render_template("kontakt.html", title="Kontakt")


@app.route("/hobby")
def hobby():
    return render_template("hobby.html", title="Hobby")


@app.route("/formularz", methods=["GET", "POST"])
def formularz():
    if request.method == "GET":
        return render_template("formularz.html", title="Formularz")

    submission = Submission(
        name=request.form.get("name", ""),
        email=request.form.get("email", ""),
        message=request.form.get("message", ""),
        created_at=datetime.utcnow().isoformat() + "Z",
    )
    errors = submission.validate()
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    items = load_submissions()
    items.append(asdict(submission))
    save_submissions(items)

    return jsonify({"ok": True, "data": asdict(submission)})


if __name__ == "__main__":
    app.run(debug=True)
