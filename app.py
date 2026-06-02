"""Thin web layer — auth routes and template rendering only.
All business logic and data mutations live in api/routes.py (REST API).
Shared DB helpers and constants live in api/db.py.
"""
import json
import logging
import os
import re
import secrets

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, session, url_for
from flask_login import (
    LoginManager, UserMixin, current_user, login_required, login_user, logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from api.db import (
    DOKUMENT_TYPY, EFEKTY_UCZENIA,
    can_edit_dok, get_db_connection, init_db,
    get_praktyki_for_role, get_praktyka_for_student, get_praktyka_by_id,
)
from api.routes import api_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
logging.basicConfig(level=logging.INFO)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLE_OPTIONS = ["student", "uopz", "zopz", "dyrektor"]
DIRECTOR_EMAIL = os.getenv("DIRECTOR_EMAIL", "").strip().lower()

app.config["MICROSOFT_CLIENT_ID"]     = os.getenv("MICROSOFT_CLIENT_ID", "")
app.config["MICROSOFT_CLIENT_SECRET"] = os.getenv("MICROSOFT_CLIENT_SECRET", "")
app.config["MICROSOFT_TENANT_ID"]     = os.getenv("MICROSOFT_TENANT_ID", "common")
app.config["MICROSOFT_REDIRECT_URI"]  = os.getenv(
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


# ── User model ─────────────────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, user_id, email, name, role, aktywny=True):
        self.id = user_id
        self.email = email
        self.name = name
        self.role = role
        self.aktywny = bool(aktywny)


def _row_to_user(row):
    if row is None:
        return None
    return User(
        user_id=row["id"], email=row["email"],
        name=f"{row['imie']} {row['nazwisko']}".strip(),
        role=row["rola"], aktywny=row["aktywny"],
    )


def _normalize_email(email):
    return (email or "").strip().lower()


def _split_name(name):
    parts = (name or "").strip().split(None, 1)
    return (parts[0] if parts else ""), (parts[1] if len(parts) > 1 else "")


def _get_user_by_email(email):
    em = _normalize_email(email)
    if not em:
        return None
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT id,imie,nazwisko,email,rola,aktywny,haslo_hash FROM uzytkownik WHERE email=?",
            (em,),
        ).fetchone()


def _get_user_by_id(user_id):
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id,imie,nazwisko,email,rola,aktywny FROM uzytkownik WHERE id=?", (uid,)
        ).fetchone()
    return _row_to_user(row)


def _ensure_ms_user(email, name):
    em = _normalize_email(email)
    if not em:
        return None
    row = _get_user_by_email(em)
    imie, nazwisko = _split_name(name)
    is_dir = DIRECTOR_EMAIL and em == DIRECTOR_EMAIL
    if row:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE uzytkownik SET imie=?,nazwisko=?,aktywny=1,rola=? WHERE email=?",
                (imie, nazwisko, "dyrektor" if is_dir else row["rola"], em),
            )
        return _get_user_by_email(em)
    role = "dyrektor" if is_dir else "student"
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO uzytkownik (imie,nazwisko,email,haslo_hash,rola,aktywny,created_at)"
            " VALUES (?,?,?,?,?,1,datetime('now'))",
            (imie, nazwisko, em, "", role),
        )
    return _get_user_by_email(em)


def _is_oauth_configured():
    return bool(app.config["MICROSOFT_CLIENT_ID"] and app.config["MICROSOFT_CLIENT_SECRET"])


@login_manager.user_loader
def load_user(user_id):
    return _get_user_by_id(user_id)


@app.context_processor
def inject_notice():
    return {"notice": session.pop("notice", None), "dev_mode": True}


init_db()


# ── Quick login helpers (for demo/presentation) ────────────────────────────────

_DEV_USERS = [
    {"email": "student1@dev.local", "imie": "Anna",   "nazwisko": "Kowalska",  "rola": "student"},
    {"email": "student2@dev.local", "imie": "Piotr",  "nazwisko": "Nowak",     "rola": "student"},
    {"email": "student3@dev.local", "imie": "Maria",  "nazwisko": "Wiśniewska","rola": "student"},
    {"email": "zopz@dev.local",     "imie": "Tomasz", "nazwisko": "Zopzowski", "rola": "zopz"},
    {"email": "uopz@dev.local",     "imie": "Ewa",    "nazwisko": "Uopzowska", "rola": "uopz"},
    {"email": "dyrektor@dev.local", "imie": "Jan",    "nazwisko": "Dyrektor",  "rola": "dyrektor"},
]


def _ensure_dev_users():
    with get_db_connection() as conn:
        for u in _DEV_USERS:
            exists = conn.execute(
                "SELECT id FROM uzytkownik WHERE email=?", (u["email"],)
            ).fetchone()
            if not exists:
                cur = conn.execute(
                    "INSERT INTO uzytkownik (imie,nazwisko,email,haslo_hash,rola,aktywny,created_at)"
                    " VALUES (?,?,?,?,?,1,datetime('now'))",
                    (u["imie"], u["nazwisko"], u["email"], "", u["rola"]),
                )
                # Create a dev zakład for the zopz user
                if u["rola"] == "zopz":
                    conn.execute(
                        "INSERT OR IGNORE INTO zaklad (nazwa,adres,nip,zopz_id,created_at)"
                        " VALUES ('DEV Zakład Sp. z o.o.','ul. Testowa 1, Elbląg','1234567890',?,datetime('now'))",
                        (cur.lastrowid,),
                    )


_ensure_dev_users()


@app.route("/dev/login/<email>")
def dev_login(email):
    row = _get_user_by_email(email)
    if not row:
        return "Nie znaleziono użytkownika dev.", 404
    login_user(_row_to_user(row))
    return redirect(url_for("dashboard"))


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profil"))
    error = None
    if request.method == "POST":
        email = _normalize_email(request.form.get("email"))
        password = request.form.get("password") or ""
        if not email or not password:
            error = "Podaj email i haslo."
        else:
            row = _get_user_by_email(email)
            if not row:
                error = "Nie znaleziono konta."
            elif not row["haslo_hash"]:
                error = "To konto korzysta z logowania Microsoft."
            elif not check_password_hash(row["haslo_hash"], password):
                error = "Nieprawidlowe haslo."
            elif not bool(row["aktywny"]):
                error = "Konto oczekuje na zatwierdzenie przez dyrektora."
            else:
                login_user(_row_to_user(row))
                session["notice"] = "Zalogowano pomyslnie."
                return redirect(url_for("profil"))
    oauth_error = None if _is_oauth_configured() else \
        "Brak konfiguracji OAuth2. Uzupelnij plik .env i zrestartuj aplikacje."
    return render_template("login.html", title="Logowanie", error=error, oauth_error=oauth_error)


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = _normalize_email(request.form.get("email"))
    password = request.form.get("password") or ""
    zaklad_name = request.form.get("zaklad_name", "").strip()
    zaklad_address = request.form.get("zaklad_address", "").strip()
    zaklad_nip = request.form.get("zaklad_nip", "").strip()

    if not all([name, email, password, zaklad_name, zaklad_address, zaklad_nip]):
        session["notice"] = "Uzupelnij wszystkie pola."
        return redirect(url_for("login"))
    if not EMAIL_RE.match(email):
        session["notice"] = "Nieprawidlowy format email."
        return redirect(url_for("login"))
    if not re.fullmatch(r"\d{10}", zaklad_nip):
        session["notice"] = "NIP musi miec 10 cyfr."
        return redirect(url_for("login"))
    if len(password) < 6:
        session["notice"] = "Haslo musi miec co najmniej 6 znakow."
        return redirect(url_for("login"))
    if _get_user_by_email(email):
        session["notice"] = "Uzytkownik o takim emailu juz istnieje."
        return redirect(url_for("login"))

    is_dir = DIRECTOR_EMAIL and email == DIRECTOR_EMAIL
    role, aktywny = ("dyrektor", True) if is_dir else ("student", False)
    imie, nazwisko = _split_name(name)
    with get_db_connection() as conn:
        cur = conn.execute(
            "INSERT INTO uzytkownik (imie,nazwisko,email,haslo_hash,rola,aktywny,created_at)"
            " VALUES (?,?,?,?,?,?,datetime('now'))",
            (imie, nazwisko, email, generate_password_hash(password), role, 1 if aktywny else 0),
        )
        conn.execute(
            "INSERT INTO zaklad (nazwa,adres,nip,zopz_id,created_at) VALUES (?,?,?,?,datetime('now'))",
            (zaklad_name, zaklad_address, zaklad_nip, cur.lastrowid),
        )
    session["notice"] = ("Konto utworzone. Mozesz sie zalogowac." if aktywny
                         else "Konto utworzone i oczekuje na zatwierdzenie przez dyrektora.")
    return redirect(url_for("login"))


@app.route("/login/microsoft")
def login_microsoft():
    if not _is_oauth_configured():
        session["notice"] = "Brak konfiguracji OAuth2."
        return redirect(url_for("login"))
    nonce = secrets.token_urlsafe(24)
    session["oauth_nonce"] = nonce
    return oauth.microsoft.authorize_redirect(app.config["MICROSOFT_REDIRECT_URI"], nonce=nonce)


@app.route("/auth/callback")
def auth_callback():
    if not _is_oauth_configured():
        session["notice"] = "Brak konfiguracji OAuth2."
        return redirect(url_for("login"))
    try:
        token = oauth.microsoft.authorize_access_token()
        nonce = session.pop("oauth_nonce", None)
        userinfo = oauth.microsoft.parse_id_token(token, nonce=nonce)
    except Exception as exc:
        app.logger.exception("OAuth callback error: %s", exc)
        session["notice"] = "Nie udalo sie zalogowac. Sprobuj ponownie."
        return redirect(url_for("login"))
    if not userinfo or not (userinfo.get("oid") or userinfo.get("sub")):
        session["notice"] = "Brak danych uzytkownika."
        return redirect(url_for("login"))
    email = userinfo.get("preferred_username") or userinfo.get("email", "")
    name = userinfo.get("name") or email or "Uzytkownik"
    urow = _ensure_ms_user(email, name)
    user = _row_to_user(urow) if urow else None
    if not user:
        session["notice"] = "Nie udalo sie utworzyc konta uzytkownika."
        return redirect(url_for("login"))
    login_user(user)
    return redirect(url_for("profil"))


@app.route("/logout")
def logout():
    logout_user()
    session["notice"] = "Wylogowano pomyslnie."
    return redirect(url_for("index"))


# ── User management ────────────────────────────────────────────────────────────

@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    error = None
    if request.method == "POST":
        role = request.form.get("role", "").strip().lower()
        if role not in ROLE_OPTIONS:
            error = "Nieprawidlowa rola."
        else:
            with get_db_connection() as conn:
                conn.execute("UPDATE uzytkownik SET rola=? WHERE id=?", (role, current_user.id))
            session["notice"] = "Rola zostala zaktualizowana."
            return redirect(url_for("profil"))
    return render_template("profil.html", title="Profil", roles=ROLE_OPTIONS, error=error)


@app.route("/zatwierdzanie")
@login_required
def approvals():
    if current_user.role != "dyrektor":
        abort(403)
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT u.id, u.imie, u.nazwisko, u.email, u.aktywny, u.created_at,"
            " z.nazwa as zaklad_nazwa"
            " FROM uzytkownik u LEFT JOIN zaklad z ON z.zopz_id=u.id"
            " WHERE u.aktywny=0 ORDER BY u.id DESC"
        ).fetchall()
    return render_template("approvals.html", title="Zatwierdzanie", users=rows)


@app.route("/zatwierdzanie/<int:user_id>/approve", methods=["POST"])
@login_required
def approve_user(user_id):
    if current_user.role != "dyrektor":
        abort(403)
    with get_db_connection() as conn:
        conn.execute("UPDATE uzytkownik SET aktywny=1, rola='zopz' WHERE id=?", (user_id,))
    session["notice"] = "Uzytkownik zostal zatwierdzony."
    return redirect(url_for("approvals"))


# ── Page rendering (thin — mutations go through /api/) ─────────────────────────

@app.route("/")
def index():
    return render_template("index.html", title="Start")


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "student":
        praktyka = get_praktyka_for_student(current_user.id, current_user)
        return render_template("dashboard.html", title="Panel", praktyka=praktyka)
    praktyki = get_praktyki_for_role(current_user)
    students, zaklady = [], []
    if current_user.role == "uopz":
        with get_db_connection() as conn:
            students = conn.execute(
                "SELECT id, imie||' '||nazwisko AS name FROM uzytkownik"
                " WHERE rola='student' AND aktywny=1 ORDER BY nazwisko,imie"
            ).fetchall()
            zaklady = conn.execute(
                "SELECT z.id, z.nazwa, u.imie||' '||u.nazwisko AS zopz_name"
                " FROM zaklad z JOIN uzytkownik u ON u.id=z.zopz_id ORDER BY z.nazwa"
            ).fetchall()
    return render_template(
        "dashboard.html", title="Panel",
        praktyki=praktyki, students=students, zaklady=zaklady,
    )


@app.route("/praktyka/<int:praktyka_id>/dziennik")
@login_required
def dziennik_view(praktyka_id):
    p = get_praktyka_by_id(praktyka_id, current_user)
    if not p:
        abort(404)
    if not (current_user.role == "dyrektor"
            or (current_user.role == "student" and current_user.id == p["student_id"])
            or (current_user.role == "uopz"    and current_user.id == p["uopz_id"])
            or (current_user.role == "zopz"    and current_user.id == p["zopz_id"])):
        abort(403)
    with get_db_connection() as conn:
        wpisy = [dict(w) for w in conn.execute(
            "SELECT * FROM wpis_dziennika WHERE praktyka_id=? ORDER BY numer_dnia", (praktyka_id,)
        ).fetchall()]
    for w in wpisy:
        try:
            w["nr_efektow"] = json.loads(w["nr_efektow"])
        except (json.JSONDecodeError, TypeError):
            w["nr_efektow"] = []
    pages = []
    for i in range(0, 120, 10):
        pe = [w for w in wpisy if i < w["numer_dnia"] <= i + 10]
        confirmed = len(pe) == 10 and all(w["potwierdzony"] for w in pe)
        pages.append({
            "num": i // 10 + 1, "from_day": i + 1, "to_day": i + 10,
            "entries": pe, "confirmed": confirmed,
            "can_confirm": (
                len(pe) == 10 and not confirmed
                and current_user.role == "zopz" and current_user.id == p["zopz_id"]
            ),
        })
    total = len(wpisy)
    confirmed_total = sum(1 for w in wpisy if w["potwierdzony"])
    return render_template(
        "dziennik.html", title="Dziennik praktyki",
        praktyka=p, pages=pages, total=total,
        confirmed_total=confirmed_total,
        can_add=(
            p["etap"] == "dziennik_aktywny"
            and current_user.role == "student"
            and current_user.id == p["student_id"]
            and total < 120
        ),
        efekty_uczenia=EFEKTY_UCZENIA,
    )


@app.route("/praktyka/<int:praktyka_id>/dokument/<typ>")
@login_required
def dokument_view(praktyka_id, typ):
    if typ not in DOKUMENT_TYPY:
        abort(404)
    p = get_praktyka_by_id(praktyka_id, current_user)
    if not p:
        abort(404)
    if not (current_user.role == "dyrektor"
            or (current_user.role == "student" and current_user.id == p["student_id"])
            or (current_user.role == "uopz"    and current_user.id == p["uopz_id"])
            or (current_user.role == "zopz"    and current_user.id == p["zopz_id"])):
        abort(403)
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT zawartosc_json, updated_at FROM dokument WHERE praktyka_id=? AND typ=?",
            (praktyka_id, typ),
        ).fetchone()
    existing, updated_at = {}, None
    if row:
        try:
            existing = json.loads(row["zawartosc_json"])
        except (json.JSONDecodeError, TypeError):
            existing = {}
        updated_at = row["updated_at"]
    zal1 = {}
    if typ == "zal3_1":
        with get_db_connection() as conn:
            r1 = conn.execute(
                "SELECT zawartosc_json FROM dokument WHERE praktyka_id=? AND typ='zal1'",
                (praktyka_id,),
            ).fetchone()
        if r1:
            try:
                zal1 = json.loads(r1["zawartosc_json"])
            except (json.JSONDecodeError, TypeError):
                zal1 = {}
    return render_template(
        "dokument.html",
        title=DOKUMENT_TYPY[typ], typ=typ, typ_label=DOKUMENT_TYPY[typ],
        praktyka=p, data=existing, updated_at=updated_at,
        can_edit=can_edit_dok(typ, p, current_user, existing),
        efekty_uczenia=EFEKTY_UCZENIA, zal1=zal1,
        oceny=[str(x / 10) for x in range(20, 55, 5)],
    )


@app.route("/kontakt")
def kontakt():
    return render_template("kontakt.html", title="Kontakt")


if __name__ == "__main__":
    app.run(debug=True)
