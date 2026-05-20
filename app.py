from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import zip_longest
import json
import os
import re

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "submissions.json")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class JournalEntry:
    date: str
    activity: str
    hours: str

    def validate(self, index):
        errors = {}
        if not self.date.strip():
            errors[f"entries.{index}.date"] = "Data jest wymagana."
        if not self.activity.strip():
            errors[f"entries.{index}.activity"] = "Opis czynnosci jest wymagany."
        if not self.hours.strip():
            errors[f"entries.{index}.hours"] = "Liczba godzin jest wymagana."
        elif not self.hours.isdigit() or int(self.hours) <= 0:
            errors[f"entries.{index}.hours"] = "Godziny musza byc liczba dodatnia."
        return errors


@dataclass
class PracticeSubmission:
    name: str
    email: str
    message: str
    entries: list[JournalEntry]
    created_at: str

    def validate(self):
        errors = {}
        if not self.name.strip():
            errors["name"] = "Imie jest wymagane."
        if not self.email.strip():
            errors["email"] = "Email jest wymagany."
        elif not EMAIL_RE.match(self.email):
            errors["email"] = "Nieprawidlowy format email."
        if not self.message.strip():
            errors["message"] = "Uwagi sa wymagane."
        if not self.entries:
            errors["entries"] = "Wymagany jest co najmniej jeden wpis dziennika."
        for index, entry in enumerate(self.entries, start=1):
            errors.update(entry.validate(index))
        return errors


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return []


def save_data(items):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2)


def parse_entries(form):
    dates = form.getlist("entry_date")
    activities = form.getlist("entry_activity")
    hours_list = form.getlist("entry_hours")

    entries = []
    for date, activity, hours in zip_longest(
        dates, activities, hours_list, fillvalue=""
    ):
        if not (date.strip() or activity.strip() or hours.strip()):
            continue
        entries.append(JournalEntry(date=date, activity=activity, hours=hours))
    return entries


@app.route("/")
def index():
    return render_template("index.html", title="Start")


@app.route("/kontakt")
def kontakt():
    return render_template("kontakt.html", title="Kontakt")


@app.route("/hobby")
def hobby():
    return render_template("hobby.html", title="Zainteresowania")


@app.route("/formularz", methods=["GET", "POST"])
def formularz():
    if request.method == "GET":
        return render_template("formularz.html", title="Formularz")

    entries = parse_entries(request.form)
    submission = PracticeSubmission(
        name=request.form.get("name", ""),
        email=request.form.get("email", ""),
        message=request.form.get("message", ""),
        entries=entries,
        created_at=datetime.utcnow().isoformat() + "Z",
    )
    errors = submission.validate()
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    items = load_data()
    items.append(asdict(submission))
    save_data(items)

    return jsonify({"ok": True, "data": asdict(submission)})


if __name__ == "__main__":
    app.run(debug=True)
