from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import zip_longest
import json
import logging
import os
import re
import secrets
import sqlite3

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from api.routes import api_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
logging.basicConfig(level=logging.INFO)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "submissions.json")
DB_FILE = os.path.join(DATA_DIR, "app.db")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLE_OPTIONS = ["student", "opiekun", "administrator"]

app.config["MICROSOFT_CLIENT_ID"] = os.getenv("MICROSOFT_CLIENT_ID", "")
app.config["MICROSOFT_CLIENT_SECRET"] = os.getenv("MICROSOFT_CLIENT_SECRET", "")
app.config["MICROSOFT_TENANT_ID"] = os.getenv("MICROSOFT_TENANT_ID", "common")
app.config["MICROSOFT_REDIRECT_URI"] = os.getenv(
    "MICROSOFT_REDIRECT_URI", "http://127.0.0.1:5000/auth/callback"
)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Zaloguj sie, aby kontynuowac."

app.register_blueprint(api_bp)

oauth = OAuth(app)
oauth.register(
    name="microsoft",
    client_id=app.config["MICROSOFT_CLIENT_ID"],
    client_secret=app.config["MICROSOFT_CLIENT_SECRET"],
    server_metadata_url=(
        "https://login.microsoftonline.com/"
        f"{app.config['MICROSOFT_TENANT_ID']}/v2.0/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile"},
)


class User(UserMixin):
    def __init__(self, user_id, email, name, role, first_login):
        self.id = user_id
        self.email = email
        self.name = name
        self.role = role
        self.first_login = bool(first_login)


def get_db_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                first_login INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )


def row_to_user(row):
    if row is None:
        return None
    return User(
        user_id=row["id"],
        email=row["email"],
        name=row["name"],
        role=row["role"],
        first_login=row["first_login"],
    )


def get_user_by_id(user_id):
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT id, email, name, role, first_login FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return row_to_user(row)


def create_user(user_id, email, name):
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (id, email, name, role, first_login, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (user_id, email, name, "student", datetime.utcnow().isoformat() + "Z"),
        )


def update_user_role(user_id, role):
    with get_db_connection() as connection:
        connection.execute(
            "UPDATE users SET role = ?, first_login = 0 WHERE id = ?",
            (role, user_id),
        )


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)


@app.context_processor
def inject_notice():
    return {"notice": session.pop("notice", None)}


init_db()


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


def is_oauth_configured():
    return bool(
        app.config["MICROSOFT_CLIENT_ID"]
        and app.config["MICROSOFT_CLIENT_SECRET"]
    )


@app.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profil"))
    error = None
    if not is_oauth_configured():
        error = (
            "Brak konfiguracji OAuth2. Uzupelnij plik .env i zrestartuj aplikacje."
        )
    return render_template("login.html", title="Logowanie", error=error)


@app.route("/login/microsoft")
def login_microsoft():
    if not is_oauth_configured():
        session["notice"] = "Brak konfiguracji OAuth2. Uzupelnij plik .env."
        return redirect(url_for("login"))
    nonce = secrets.token_urlsafe(24)
    session["oauth_nonce"] = nonce
    redirect_uri = app.config["MICROSOFT_REDIRECT_URI"]
    return oauth.microsoft.authorize_redirect(redirect_uri, nonce=nonce)


@app.route("/auth/callback")
def auth_callback():
    if not is_oauth_configured():
        session["notice"] = "Brak konfiguracji OAuth2. Uzupelnij plik .env."
        return redirect(url_for("login"))
    try:
        token = oauth.microsoft.authorize_access_token()
        nonce = session.pop("oauth_nonce", None)
        userinfo = oauth.microsoft.parse_id_token(token, nonce=nonce)
    except Exception as exc:
        app.logger.exception("OAuth callback error: %s", exc)
        session["notice"] = "Nie udalo sie zalogowac. Sprobuj ponownie."
        return redirect(url_for("login"))

    if not userinfo:
        session["notice"] = "Nie udalo sie odczytac danych uzytkownika."
        return redirect(url_for("login"))

    user_id = userinfo.get("oid") or userinfo.get("sub")
    email = userinfo.get("preferred_username") or userinfo.get("email", "")
    name = userinfo.get("name") or email or "Uzytkownik"

    if not user_id:
        session["notice"] = "Brak identyfikatora uzytkownika w danych logowania."
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if user is None:
        create_user(user_id, email, name)
        user = get_user_by_id(user_id)

    login_user(user)
    if user and user.first_login:
        session["notice"] = "Pierwsze logowanie - wybierz role w profilu."
    return redirect(url_for("profil"))


@app.route("/logout")
def logout():
    logout_user()
    session["notice"] = "Wylogowano pomyslnie."
    return redirect(url_for("index"))


@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    error = None
    if request.method == "POST":
        role = request.form.get("role", "").strip().lower()
        if role not in ROLE_OPTIONS:
            error = "Nieprawidlowa rola. Wybierz jedna z listy."
        else:
            update_user_role(current_user.id, role)
            session["notice"] = "Rola zostala zaktualizowana."
            return redirect(url_for("profil"))
    return render_template(
        "profil.html",
        title="Profil",
        roles=ROLE_OPTIONS,
        error=error,
    )


@app.route("/")
def index():
    return render_template("index.html", title="Start")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", title="Panel")


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
