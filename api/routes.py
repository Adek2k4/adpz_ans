"""REST API blueprint — all business logic lives here."""
import json
from datetime import datetime

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user

from .db import (
    DOKUMENT_TYPY, ETAPY, ETAP_IDX,
    can_edit_dok, get_db_connection, get_praktyka_by_id,
    get_praktyki_for_role, get_praktyka_for_student, parse_dok,
)

# Required signatures for each stage before advancing
_REQUIRED_SIGS = {
    # Both sides must sign zal1+zal2 before leaving stage 0.
    # Stage 1 has the same requirements so _try_auto_advance skips it immediately.
    "dyrektor_wysyla_wstepne": [
        ("zal1", "podpis_zaklad"), ("zal1", "podpis_uczelnia"),
        ("zal2", "podpis_zakladu"), ("zal2", "podpis_dyrektora"),
    ],
    "zopz_podpisuje_wstepne": [
        ("zal1", "podpis_zaklad"), ("zal1", "podpis_uczelnia"),
        ("zal2", "podpis_zakladu"), ("zal2", "podpis_dyrektora"),
    ],
    "zopz_wypelnia_zal2a":     [("zal2a", "podpis_zopz")],
    "student_podpisuje_zal2a": [("zal2a", "podpis_student")],
    "uopz_podpisuje_zal2a":    [("zal2a", "podpis_uopz")],
    "dyrektor_wysyla_zal3_1":  [("zal3_1", "podpis_dyrektor")],
    "zopz_podpisuje_zal3_2":   [("zal3_2", "podpis_zopz_1"), ("zal3_2", "podpis_zopz_2")],
    "zal7_do_podpisania":      [("zal7", "podpis_student")],
    "dokumenty_koncowe": [
        ("zal3_3", "podpis_zopz"), ("zal3_4", "podpis_zopz"),
        ("zal3_5", "podpis_uopz"), ("zal3_6", "podpis_uopz"),
        ("zal4", "podpis_zopz"), ("zal4", "podpis_uopz"),
        ("zal5", None),
    ],
    "dyrektor_podpisuje_zal8": [("zal8", "podpis_dyrektor")],
}


def _missing_docs(pid, etap_id, conn):
    """Return list of human-readable strings for unsatisfied requirements."""
    missing = []
    for typ, sig_field in _REQUIRED_SIGS.get(etap_id, []):
        row = conn.execute(
            "SELECT zawartosc_json FROM dokument WHERE praktyka_id=? AND typ=?", (pid, typ)
        ).fetchone()
        label = DOKUMENT_TYPY.get(typ, typ)
        if not row:
            missing.append(f"{label}: brak dokumentu")
            continue
        try:
            data = json.loads(row["zawartosc_json"])
        except Exception:
            data = {}
        if sig_field is None:
            if not data:
                missing.append(f"{label}: dokument pusty")
        elif not data.get(sig_field):
            missing.append(f"{label}: brak podpisu")
    return missing


def _try_auto_advance(pid, etap_id, conn):
    """Auto-advance praktyka to next stage if all doc requirements are met.
    Recurses so that stages whose requirements are already satisfied are
    also skipped (e.g. stage 1 after stage 0 when both parties already signed).
    Returns the final new etap id or None if no advance happened."""
    if etap_id not in _REQUIRED_SIGS:
        return None
    if _missing_docs(pid, etap_id, conn):
        return None
    idx = ETAP_IDX.get(etap_id, -1)
    if idx < 0 or idx + 1 >= len(ETAPY):
        return None
    next_etap = ETAPY[idx + 1]["id"]
    conn.execute(
        "UPDATE praktyka SET etap=?, updated_at=? WHERE id=?",
        (next_etap, _NOW(), pid),
    )
    # Recursively skip stages whose requirements are already met
    further = _try_auto_advance(pid, next_etap, conn)
    return further or next_etap

api_bp = Blueprint("api", __name__)

_NOW = lambda: datetime.utcnow().isoformat() + "Z"


def _ok(data=None, status=200):
    return jsonify({"ok": True, **({"data": data} if data is not None else {})}), status


def _err(message, status=400, details=None):
    payload = {"ok": False, "error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status


def _auth():
    """Return 401 error response if the request is not authenticated."""
    if not current_user.is_authenticated:
        return _err("Nie zalogowano.", 401)
    return None


def _involved(p):
    """Check whether current_user is a participant of praktyka p."""
    u = current_user
    return (
        u.role == "dyrektor"
        or (u.role == "student" and u.id == p["student_id"])
        or (u.role == "uopz"    and u.id == p["uopz_id"])
        or (u.role == "zopz"    and u.id == p["zopz_id"])
    )


# ── Praktyki ──────────────────────────────────────────────────────────────────

@api_bp.route("/api/praktyki", methods=["GET"])
def api_praktyki_list():
    if e := _auth(): return e
    if current_user.role == "student":
        p = get_praktyka_for_student(current_user.id, current_user)
        return _ok([p] if p else [])
    return _ok(get_praktyki_for_role(current_user))


@api_bp.route("/api/praktyki", methods=["POST"])
def api_praktyki_create():
    if e := _auth(): return e
    if current_user.role != "uopz":
        return _err("Tylko UOPZ może tworzyć praktyki.", 403)

    if request.is_json:
        data = request.get_json(silent=True) or {}
        student_id = data.get("student_id")
        zaklad_id  = data.get("zaklad_id")
        data_od    = (data.get("data_od") or "").strip()
        data_do    = (data.get("data_do") or "").strip()
    else:
        student_id = request.form.get("student_id")
        zaklad_id  = request.form.get("zaklad_id")
        data_od    = (request.form.get("data_od") or "").strip()
        data_do    = (request.form.get("data_do") or "").strip()

    if not all([student_id, zaklad_id, data_od, data_do]):
        return _err("Wymagane pola: student_id, zaklad_id, data_od, data_do.")

    try:
        student_id = int(student_id)
        zaklad_id  = int(zaklad_id)
    except (TypeError, ValueError):
        return _err("student_id i zaklad_id muszą być liczbami.")

    now = _NOW()
    with get_db_connection() as conn:
        cur = conn.execute(
            """INSERT INTO praktyka
               (student_id, uopz_id, zaklad_id, data_rozpoczecia, data_zakonczenia, etap, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'dyrektor_wysyla_wstepne', ?, ?)""",
            (student_id, current_user.id, zaklad_id, data_od, data_do, now, now),
        )
    p = get_praktyka_by_id(cur.lastrowid, current_user)
    return _ok(p, 201)


@api_bp.route("/api/praktyki/<int:pid>", methods=["GET"])
def api_praktyka_get(pid):
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p or not _involved(p):
        return _err("Nie znaleziono.", 404)
    return _ok(p)


@api_bp.route("/api/praktyki/<int:pid>/dane-studenta", methods=["PUT", "POST"])
def api_dane_studenta(pid):
    """Student sets nr albumu and specjalność – shared across all documents."""
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p or not _involved(p):
        return _err("Nie znaleziono.", 404)
    if current_user.role != "student" or current_user.id != p["student_id"]:
        return _err("Tylko student może edytować te dane.", 403)

    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form
    nr_albumu   = (data.get("nr_albumu") or "").strip()
    specjalnosc = (data.get("specjalnosc") or "").strip()

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE praktyka SET nr_albumu=?, specjalnosc=?, updated_at=? WHERE id=?",
            (nr_albumu, specjalnosc, _NOW(), pid),
        )
    return _ok({"nr_albumu": nr_albumu, "specjalnosc": specjalnosc,
                "message": "Dane studenta zapisane."})


@api_bp.route("/api/praktyki/<int:pid>/akcja", methods=["POST"])
def api_praktyka_akcja(pid):
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p or not _involved(p):
        return _err("Nie znaleziono.", 404)

    data  = request.get_json(silent=True) or {}
    akcja = data.get("akcja", "zatwierdz")

    if akcja == "odrzuc":
        if not p["can_reject"]:
            return _err("Brak uprawnień do odrzucenia.", 403)
        next_etap = "zopz_wypelnia_zal2a"
        msg = "Harmonogram odrzucony – odesłano do ZOPZu."
        with get_db_connection() as conn:
            conn.execute("UPDATE praktyka SET etap=?, updated_at=? WHERE id=?",
                         (next_etap, _NOW(), pid))
    else:
        if not p["can_act"]:
            return _err("Brak uprawnień do wykonania tej akcji.", 403)
        idx = p["etap_idx"]
        next_etap = ETAPY[idx + 1]["id"] if idx + 1 < len(ETAPY) else p["etap"]
        msg = "Akcja wykonana pomyślnie."
        with get_db_connection() as conn:
            missing = _missing_docs(pid, p["etap"], conn)
            if missing:
                return _err(
                    "Brak wymaganych dokumentów lub podpisów.",
                    409,
                    {"brakujace": missing},
                )
            conn.execute("UPDATE praktyka SET etap=?, updated_at=? WHERE id=?",
                         (next_etap, _NOW(), pid))

    return _ok({"etap": next_etap, "message": msg})


# ── Dziennik ──────────────────────────────────────────────────────────────────

@api_bp.route("/api/praktyki/<int:pid>/dziennik", methods=["GET"])
def api_dziennik_list(pid):
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p or not _involved(p):
        return _err("Nie znaleziono.", 404)

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM wpis_dziennika WHERE praktyka_id = ? ORDER BY numer_dnia",
            (pid,),
        ).fetchall()

    wpisy = []
    for w in rows:
        wd = dict(w)
        try:
            wd["nr_efektow"] = json.loads(wd["nr_efektow"])
        except (json.JSONDecodeError, TypeError):
            wd["nr_efektow"] = []
        wpisy.append(wd)

    # group into pages of 10 with confirmation status
    pages = []
    for i in range(0, 120, 10):
        page_entries = [w for w in wpisy if i < w["numer_dnia"] <= i + 10]
        confirmed = len(page_entries) == 10 and all(w["potwierdzony"] for w in page_entries)
        pages.append({
            "num": i // 10 + 1,
            "from_day": i + 1,
            "to_day": i + 10,
            "entries": page_entries,
            "confirmed": confirmed,
            "can_confirm": (
                len(page_entries) == 10
                and not confirmed
                and current_user.role == "zopz"
                and current_user.id == p["zopz_id"]
            ),
        })

    return _ok({
        "total": len(wpisy),
        "confirmed_total": sum(1 for w in wpisy if w["potwierdzony"]),
        "pages": pages,
    })


@api_bp.route("/api/praktyki/<int:pid>/dziennik", methods=["POST"])
def api_dziennik_add(pid):
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p:
        return _err("Nie znaleziono.", 404)
    if p["etap"] != "dziennik_aktywny":
        return _err("Dziennik nie jest aktywny.", 409)
    if current_user.role != "student" or current_user.id != p["student_id"]:
        return _err("Tylko student może dodawać wpisy.", 403)

    # Accept JSON or form data
    if request.is_json:
        data = request.get_json() or {}
        data_wpisu   = (data.get("data_wpisu") or "").strip()
        opis_prac    = (data.get("opis_prac") or "").strip()
        nr_efektow   = data.get("nr_efektow", [])
    else:
        data_wpisu   = (request.form.get("data_wpisu") or "").strip()
        opis_prac    = (request.form.get("opis_prac") or "").strip()
        nr_efektow   = request.form.getlist("nr_efektow")

    if not data_wpisu or not opis_prac:
        return _err("Wymagane pola: data_wpisu, opis_prac.")

    now = _NOW()
    with get_db_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM wpis_dziennika WHERE praktyka_id = ?", (pid,)
        ).fetchone()[0]
        if total >= 120:
            return _err("Dziennik jest już pełny (120 wpisów).", 409)
        numer = total + 1
        conn.execute(
            """INSERT INTO wpis_dziennika
               (praktyka_id, numer_dnia, data_wpisu, opis_prac, nr_efektow, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (pid, numer, data_wpisu, opis_prac,
             json.dumps(nr_efektow, ensure_ascii=False), now),
        )

    return _ok({"numer_dnia": numer, "message": f"Wpis nr {numer} dodany."}, 201)


@api_bp.route("/api/praktyki/<int:pid>/dziennik/strony/<int:page_num>/zatwierdz", methods=["POST"])
def api_dziennik_zatwierdz(pid, page_num):
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p:
        return _err("Nie znaleziono.", 404)
    if p["etap"] != "dziennik_aktywny":
        return _err("Dziennik nie jest aktywny.", 409)
    if current_user.role != "zopz" or current_user.id != p["zopz_id"]:
        return _err("Tylko ZOPZ zakładu może zatwierdzać strony.", 403)
    if not 1 <= page_num <= 12:
        return _err("Numer strony musi być w zakresie 1–12.", 400)

    day_from = (page_num - 1) * 10 + 1
    day_to   = page_num * 10
    now      = _NOW()

    with get_db_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM wpis_dziennika WHERE praktyka_id=? AND numer_dnia BETWEEN ? AND ?",
            (pid, day_from, day_to),
        ).fetchone()[0]
        if count < 10:
            return _err(f"Strona {page_num} ma tylko {count}/10 wpisów.", 409)

        conn.execute(
            "UPDATE wpis_dziennika SET potwierdzony=1, potwierdzone_at=?"
            " WHERE praktyka_id=? AND numer_dnia BETWEEN ? AND ?",
            (now, pid, day_from, day_to),
        )

        confirmed_total = int(conn.execute(
            "SELECT COALESCE(SUM(potwierdzony),0) FROM wpis_dziennika WHERE praktyka_id=?",
            (pid,),
        ).fetchone()[0] or 0)

        auto_advanced = False
        if confirmed_total >= 120:
            conn.execute(
                "UPDATE praktyka SET etap='zal7_do_podpisania', updated_at=? WHERE id=?",
                (now, pid),
            )
            auto_advanced = True

    return _ok({
        "confirmed_total": confirmed_total,
        "auto_advanced": auto_advanced,
        "message": (
            f"Strona {page_num} zatwierdzona. Dziennik zakończony – odblokowano zał7."
            if auto_advanced else
            f"Strona {page_num} zatwierdzona ({confirmed_total}/120)."
        ),
    })


# ── Dokumenty ─────────────────────────────────────────────────────────────────

@api_bp.route("/api/praktyki/<int:pid>/dokumenty/<typ>/pdf", methods=["GET"])
def api_dokument_pdf(pid, typ):
    if e := _auth(): return e
    from .pdf_docs import GENERATORS
    if typ not in GENERATORS:
        return _err("Brak generatora PDF dla tego dokumentu.", 404)
    p = get_praktyka_by_id(pid, current_user)
    if not p or not _involved(p):
        return _err("Nie znaleziono.", 404)

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT zawartosc_json FROM dokument WHERE praktyka_id=? AND typ=?",
            (pid, typ),
        ).fetchone()

    dok = {}
    if row:
        try:
            dok = json.loads(row["zawartosc_json"])
        except (json.JSONDecodeError, TypeError):
            dok = {}

    # zal3_1 pulls porozumienie nr/data from zal1 if missing
    if typ == "zal3_1" and (not dok.get("nr_porozumienia") or not dok.get("data_porozumienia")):
        with get_db_connection() as conn:
            r1 = conn.execute(
                "SELECT zawartosc_json FROM dokument WHERE praktyka_id=? AND typ='zal1'", (pid,)
            ).fetchone()
        if r1:
            try:
                z1 = json.loads(r1["zawartosc_json"])
                dok.setdefault("nr_porozumienia", z1.get("numer", ""))
                dok.setdefault("data_porozumienia", z1.get("data", ""))
            except (json.JSONDecodeError, TypeError):
                pass

    pdf_bytes = GENERATORS[typ](dict(p), dok)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={typ}_praktyka{pid}.pdf"},
    )


@api_bp.route("/api/praktyki/<int:pid>/dziennik/pdf", methods=["GET"])
def api_dziennik_pdf(pid):
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p or not _involved(p):
        return _err("Nie znaleziono.", 404)

    with get_db_connection() as conn:
        wpisy = [dict(w) for w in conn.execute(
            "SELECT * FROM wpis_dziennika WHERE praktyka_id=? ORDER BY numer_dnia", (pid,)
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
        })

    from .pdf_docs import gen_dziennik
    pdf_bytes = gen_dziennik(dict(p), wpisy, pages)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=dziennik_praktyka{pid}.pdf"},
    )


@api_bp.route("/api/praktyki/<int:pid>/dokumenty/<typ>", methods=["GET"])
def api_dokument_get(pid, typ):
    if e := _auth(): return e
    if typ not in DOKUMENT_TYPY:
        return _err("Nieznany typ dokumentu.", 404)
    p = get_praktyka_by_id(pid, current_user)
    if not p or not _involved(p):
        return _err("Nie znaleziono.", 404)

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT zawartosc_json, updated_at FROM dokument WHERE praktyka_id=? AND typ=?",
            (pid, typ),
        ).fetchone()

    data, updated_at = {}, None
    if row:
        try:
            data = json.loads(row["zawartosc_json"])
        except (json.JSONDecodeError, TypeError):
            data = {}
        updated_at = row["updated_at"]

    # For zal3_1 include zal1 data for auto-fill
    zal1 = {}
    if typ == "zal3_1":
        with get_db_connection() as conn:
            r1 = conn.execute(
                "SELECT zawartosc_json FROM dokument WHERE praktyka_id=? AND typ='zal1'", (pid,)
            ).fetchone()
        if r1:
            try:
                zal1 = json.loads(r1["zawartosc_json"])
            except (json.JSONDecodeError, TypeError):
                zal1 = {}

    return _ok({
        "typ": typ, "typ_label": DOKUMENT_TYPY[typ],
        "can_edit": can_edit_dok(typ, p, current_user),
        "data": data, "updated_at": updated_at,
        "zal1": zal1,
    })


@api_bp.route("/api/praktyki/<int:pid>/dokumenty/<typ>", methods=["PUT", "POST"])
def api_dokument_save(pid, typ):
    if e := _auth(): return e
    if typ not in DOKUMENT_TYPY:
        return _err("Nieznany typ dokumentu.", 404)
    p = get_praktyka_by_id(pid, current_user)
    if not p or not _involved(p):
        return _err("Nie znaleziono.", 404)

    now = _NOW()
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT zawartosc_json FROM dokument WHERE praktyka_id=? AND typ=?", (pid, typ)
        ).fetchone()
        existing = {}
        if row:
            try:
                existing = json.loads(row["zawartosc_json"])
            except (json.JSONDecodeError, TypeError):
                existing = {}

        if not can_edit_dok(typ, p, current_user, existing):
            return _err("Brak uprawnień lub dokument już podpisany.", 403)

        form = request.get_json(silent=True) or request.form
        parsed = parse_dok(typ, form, existing, current_user)

        conn.execute(
            """INSERT INTO dokument (praktyka_id, typ, zawartosc_json, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(praktyka_id, typ)
               DO UPDATE SET zawartosc_json=excluded.zawartosc_json,
                             updated_at=excluded.updated_at""",
            (pid, typ, json.dumps(parsed, ensure_ascii=False), now),
        )

        new_etap = _try_auto_advance(pid, p["etap"], conn)

    return _ok({
        "typ": typ, "data": parsed, "updated_at": now,
        "advanced": bool(new_etap), "new_etap": new_etap,
    })


# ── Reference data ─────────────────────────────────────────────────────────────

@api_bp.route("/api/zaklady", methods=["GET"])
def api_zaklady():
    if e := _auth(): return e
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT z.id, z.nazwa, z.adres, z.nip,"
            " u.id AS zopz_id, u.imie || ' ' || u.nazwisko AS zopz_name"
            " FROM zaklad z JOIN uzytkownik u ON u.id = z.zopz_id ORDER BY z.nazwa"
        ).fetchall()
    return _ok([dict(r) for r in rows])


@api_bp.route("/api/uzytkownicy", methods=["GET"])
def api_uzytkownicy():
    if e := _auth(): return e
    rola = request.args.get("rola")
    with get_db_connection() as conn:
        if rola:
            rows = conn.execute(
                "SELECT id, imie || ' ' || nazwisko AS name, email, rola"
                " FROM uzytkownik WHERE rola=? AND aktywny=1 ORDER BY nazwisko, imie",
                (rola,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, imie || ' ' || nazwisko AS name, email, rola"
                " FROM uzytkownik WHERE aktywny=1 ORDER BY rola, nazwisko, imie"
            ).fetchall()
    return _ok([dict(r) for r in rows])


@api_bp.route("/api/me", methods=["GET"])
def api_me():
    if e := _auth(): return e
    return _ok({
        "id": current_user.id, "name": current_user.name,
        "email": current_user.email, "role": current_user.role,
    })


# ── Dziennik – edit entry ──────────────────────────────────────────────────────

@api_bp.route("/api/praktyki/<int:pid>/dziennik/<int:numer_dnia>", methods=["PUT"])
def api_dziennik_edit(pid, numer_dnia):
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p:
        return _err("Nie znaleziono.", 404)
    if current_user.role != "student" or current_user.id != p["student_id"]:
        return _err("Tylko student może edytować wpisy.", 403)
    if p["etap"] != "dziennik_aktywny":
        return _err("Dziennik nie jest aktywny.", 409)

    page_num = (numer_dnia - 1) // 10 + 1
    day_from = (page_num - 1) * 10 + 1
    day_to   = page_num * 10

    with get_db_connection() as conn:
        confirmed_count = conn.execute(
            "SELECT COUNT(*) FROM wpis_dziennika"
            " WHERE praktyka_id=? AND numer_dnia BETWEEN ? AND ? AND potwierdzony=1",
            (pid, day_from, day_to),
        ).fetchone()[0]
        if confirmed_count > 0:
            return _err("Strona jest już zatwierdzona.", 409)

        entry = conn.execute(
            "SELECT id FROM wpis_dziennika WHERE praktyka_id=? AND numer_dnia=?",
            (pid, numer_dnia),
        ).fetchone()
        if not entry:
            return _err("Wpis nie istnieje.", 404)

        if request.is_json:
            data = request.get_json() or {}
            data_wpisu = (data.get("data_wpisu") or "").strip()
            opis_prac  = (data.get("opis_prac") or "").strip()
            nr_efektow = data.get("nr_efektow", [])
        else:
            data_wpisu = (request.form.get("data_wpisu") or "").strip()
            opis_prac  = (request.form.get("opis_prac") or "").strip()
            nr_efektow = request.form.getlist("nr_efektow")

        if not data_wpisu or not opis_prac:
            return _err("Wymagane pola: data_wpisu, opis_prac.")

        conn.execute(
            "UPDATE wpis_dziennika"
            " SET data_wpisu=?, opis_prac=?, nr_efektow=?"
            " WHERE praktyka_id=? AND numer_dnia=?",
            (data_wpisu, opis_prac,
             json.dumps(nr_efektow, ensure_ascii=False),
             pid, numer_dnia),
        )

    return _ok({"numer_dnia": numer_dnia, "message": f"Wpis nr {numer_dnia} zaktualizowany."})


# ── DEV: bulk-fill journal ─────────────────────────────────────────────────────

@api_bp.route("/api/praktyki/<int:pid>/dev/wypelnij_dziennik", methods=["POST"])
def api_dev_fill_dziennik(pid):
    if e := _auth(): return e
    p = get_praktyka_by_id(pid, current_user)
    if not p:
        return _err("Nie znaleziono.", 404)
    if current_user.role != "student" or current_user.id != p["student_id"]:
        return _err("Tylko student.", 403)

    from datetime import date as _date, timedelta
    start = _date.fromisoformat(p["data_rozpoczecia"])
    now   = _NOW()

    with get_db_connection() as conn:
        existing = {r[0] for r in conn.execute(
            "SELECT numer_dnia FROM wpis_dziennika WHERE praktyka_id=?", (pid,)
        ).fetchall()}

        added = 0
        for numer in range(1, 121):
            if numer in existing:
                continue
            entry_date = (start + timedelta(days=numer - 1)).isoformat()
            conn.execute(
                "INSERT OR IGNORE INTO wpis_dziennika"
                " (praktyka_id, numer_dnia, data_wpisu, opis_prac, nr_efektow, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (pid, numer, entry_date,
                 f"Wpis testowy nr {numer} – praca w zakładzie.",
                 json.dumps(["01", "02"]), now),
            )
            added += 1

    return _ok({"added": added, "message": f"Dodano {added} wpisów testowych."})
