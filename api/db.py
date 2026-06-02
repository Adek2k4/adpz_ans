"""Shared database helpers, constants and init logic for the whole application."""
import json
import os
import sqlite3
from datetime import datetime

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DB_FILE = os.path.join(DATA_DIR, "app.db")


def get_db_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ── Workflow stages ────────────────────────────────────────────────────────────

ETAPY = [
    {"id": "dyrektor_wysyla_wstepne",  "label": "Oczekuje podpisu dyrektora (zał1, zał2)",                    "role": "dyrektor", "button": "Podpisz i wyślij załączniki wstępne (zał1, zał2)",         "can_reject": False},
    {"id": "zopz_podpisuje_wstepne",   "label": "Oczekuje podpisu ZOPZu (zał1, zał2)",                        "role": "zopz",     "button": "Podpisz i odeślij załączniki wstępne (zał1, zał2)",        "can_reject": False},
    {"id": "zopz_wypelnia_zal2a",      "label": "ZOPZ wypełnia harmonogram (zał2a)",                          "role": "zopz",     "button": "Wyślij harmonogram do podpisu studenta",                    "can_reject": False},
    {"id": "student_podpisuje_zal2a",  "label": "Oczekuje podpisu studenta (zał2a)",                          "role": "student",  "button": "Podpisz harmonogram (zał2a)",                               "can_reject": False},
    {"id": "uopz_podpisuje_zal2a",     "label": "Oczekuje podpisu UOPZu (zał2a)",                             "role": "uopz",     "button": "Podpisz harmonogram (zał2a)",                               "can_reject": True,  "reject_button": "Odrzuć i odeślij do ZOPZu"},
    {"id": "dyrektor_wysyla_zal3_1",   "label": "Oczekuje skierowania od dyrektora (zał3.1)",                 "role": "dyrektor", "button": "Podpisz i wyślij skierowanie (zał3.1)",                     "can_reject": False},
    {"id": "zopz_podpisuje_zal3_2",    "label": "Oczekuje podpisu ZOPZu – szkolenie BHP (zał3.2)",           "role": "zopz",     "button": "Zatwierdź szkolenie BHP (zał3.2)",                          "can_reject": False},
    {"id": "dziennik_aktywny",         "label": "Dziennik praktyki w trakcie",                                "role": None,       "button": None,                                                        "can_reject": False},
    {"id": "zal7_do_podpisania",       "label": "Student wypełnia sprawozdanie (zał7)",                       "role": "student",  "button": "Złóż sprawozdanie (zał7)",                                  "can_reject": False},
    {"id": "dokumenty_koncowe",        "label": "Kompletowanie dokumentacji końcowej (zał3.3–3.6, zał4, zał5)", "role": "uopz",   "button": "Dokumentacja kompletna – prześlij do protokołu (zał8)",    "can_reject": False},
    {"id": "dyrektor_podpisuje_zal8",  "label": "Oczekuje protokołu zaliczenia od dyrektora (zał8)",         "role": "dyrektor", "button": "Podpisz protokół zaliczenia (zał8)",                        "can_reject": False},
    {"id": "uopz_zamyka",              "label": "Oczekuje zamknięcia praktyki przez UOPZu",                   "role": "uopz",     "button": "Zamknij praktykę",                                          "can_reject": False},
    {"id": "zamknieta",                "label": "Praktyka zakończona",                                        "role": None,       "button": None,                                                        "can_reject": False},
]
ETAP_IDX = {e["id"]: i for i, e in enumerate(ETAPY)}

# ── Learning effects ───────────────────────────────────────────────────────────

EFEKTY_UCZENIA = [
    ("01", "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych"),
    ("02", "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce"),
    ("03", "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy"),
    ("04", "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka"),
    ("05", "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami publikowanymi w języku polskim jak i angielskim"),
    ("06", "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje, wiedzę i umiejętności, co najmniej z dwóch zakresów: sprzęt i oprogramowanie"),
    ("07", "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia"),
    ("08", "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować"),
    ("09", "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności informatycznej zakładu pracy/instytucji stosując normy i standardy stosowane w informatyce oraz biorąc pod uwagę aspekty środowiskowe i etyczne"),
    ("10", "Pracuje w zespole zajmującym się zawodowo branżą IT"),
    ("11", "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów"),
    ("12", "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji planowanego zadania, jak i przekazać im w sposób zrozumiały informacje i opinie z zakresu informatyki"),
    ("13", "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków w szczególności ekonomiczne i społeczne"),
]

# ── Document types ─────────────────────────────────────────────────────────────

DOKUMENT_TYPY = {
    "zal1":   "Załącznik nr 1 – Porozumienie",
    "zal2":   "Załącznik nr 2 – Program praktyki",
    "zal2a":  "Załącznik nr 2a – Program i harmonogram",
    "zal3_1": "Załącznik nr 3.1 – Skierowanie na praktykę",
    "zal3_2": "Załącznik nr 3.2 – Szkolenie BHP",
    "zal3_3": "Załącznik nr 3.3 – Zaświadczenie odbycia praktyki",
    "zal3_4": "Załącznik nr 3.4 – Ocena przebiegu praktyki (ZOPZ)",
    "zal3_5": "Załącznik nr 3.5 – Ocena przebiegu praktyki (UOPZ)",
    "zal3_6": "Załącznik nr 3.6 – Ocena sprawozdania z praktyki",
    "zal4":   "Załącznik nr 4 – Potwierdzenie efektów uczenia się",
    "zal5":   "Załącznik nr 5 – Kwestionariusz ankiety",
    "zal7":   "Załącznik nr 7 – Sprawozdanie studenta z praktyki",
    "zal8":   "Załącznik nr 8 – Protokół zaliczenia praktyki",
}

# Etap index from which each document becomes accessible
DOKUMENT_AVAILABLE_FROM_IDX = {
    "zal1": 0, "zal2": 0, "zal2a": 2,
    "zal3_1": 5, "zal3_2": 6,
    "zal7": 8,
    "zal3_3": 9, "zal3_4": 9, "zal3_5": 9, "zal3_6": 9, "zal4": 9, "zal5": 9,
    "zal8": 10,
}

# Etap indices at which a document is "active" (requires current attention)
DOKUMENT_CURRENT_AT = {
    "zal1":   (0, 1),
    "zal2":   (0, 1),
    "zal2a":  (2, 3, 4),
    "zal3_1": (5,),
    "zal3_2": (6,),
    "zal7":   (8,),
    "zal3_3": (9,), "zal3_4": (9,), "zal3_5": (9,), "zal3_6": (9,),
    "zal4":   (9,), "zal5":   (9,),
    "zal8":   (10,),
}

_DOK_TYPY_ALL = list(DOKUMENT_TYPY.keys())

# ── Internship query ───────────────────────────────────────────────────────────

_PRAKTYKA_SQL = """
    SELECT
        p.id, p.etap, p.data_rozpoczecia, p.data_zakonczenia,
        s.id  AS student_id,  (s.imie  || ' ' || s.nazwisko)  AS student_name,
        u.id  AS uopz_id,     (u.imie  || ' ' || u.nazwisko)  AS uopz_name,
        z.id  AS zaklad_id,   z.nazwa                          AS zaklad_nazwa,
        zo.id AS zopz_id,     (zo.imie || ' ' || zo.nazwisko) AS zopz_name
    FROM praktyka p
    JOIN uzytkownik s  ON s.id  = p.student_id
    JOIN uzytkownik u  ON u.id  = p.uopz_id
    JOIN zaklad     z  ON z.id  = p.zaklad_id
    JOIN uzytkownik zo ON zo.id = z.zopz_id
"""


def _compute_zal_statuses(etap_idx):
    zaly = [
        ("zał1",          0,  2),
        ("zał2",          0,  2),
        ("zał2a",         2,  5),
        ("zał3.1",        5,  6),
        ("zał3.2",        6,  7),
        ("dziennik",      7,  8),
        ("zał7",          8,  9),
        ("zał3.3–5/4/5",  9, 10),
        ("zał8",         10, 12),
    ]
    result = []
    for name, active_from, done_from in zaly:
        if etap_idx >= done_from:
            result.append({"name": name, "status": "done"})
        elif etap_idx >= active_from:
            result.append({"name": name, "status": "active"})
        else:
            result.append({"name": name, "status": "waiting"})
    return result


def _enrich_praktyka(row, user, conn=None):
    p = dict(row)
    idx = ETAP_IDX.get(p["etap"], 0)
    etap_info = dict(ETAPY[idx])
    p["etap_idx"] = idx
    p["zal_statuses"] = _compute_zal_statuses(idx)
    _current_typs = {
        typ for typ, idxs in DOKUMENT_CURRENT_AT.items()
        if idx in idxs and idx >= DOKUMENT_AVAILABLE_FROM_IDX[typ]
    }
    p["docs_available"] = [
        (typ, label, "current" if typ in _current_typs else "past")
        for typ, label in DOKUMENT_TYPY.items()
        if idx >= DOKUMENT_AVAILABLE_FROM_IDX[typ]
    ]
    p["dziennik_total"] = 0
    p["dziennik_confirmed"] = 0
    if p["etap"] == "dziennik_aktywny" and conn is not None:
        stats = conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(potwierdzony),0) AS confirmed"
            " FROM wpis_dziennika WHERE praktyka_id = ?",
            (p["id"],),
        ).fetchone()
        p["dziennik_total"] = stats["total"] or 0
        p["dziennik_confirmed"] = int(stats["confirmed"] or 0)
        etap_info["label"] = (
            f"Dziennik praktyki w trakcie ({p['dziennik_confirmed']}/120 wpisów potwierdzonych)"
        )
    p["etap_info"] = etap_info

    role = etap_info["role"]
    if role is None:
        p["can_act"] = False
        p["can_reject"] = False
    elif role == "dyrektor":
        p["can_act"] = user.role == "dyrektor"
        p["can_reject"] = False
    elif role == "zopz":
        p["can_act"] = user.role == "zopz" and user.id == p["zopz_id"]
        p["can_reject"] = False
    elif role == "student":
        p["can_act"] = user.role == "student" and user.id == p["student_id"]
        p["can_reject"] = False
    elif role == "uopz":
        p["can_act"] = user.role == "uopz" and user.id == p["uopz_id"]
        p["can_reject"] = p["can_act"] and etap_info.get("can_reject", False)
    else:
        p["can_act"] = False
        p["can_reject"] = False

    return p


def get_praktyki_for_role(user):
    with get_db_connection() as conn:
        if user.role == "dyrektor":
            rows = conn.execute(_PRAKTYKA_SQL + " ORDER BY p.created_at DESC").fetchall()
        elif user.role == "uopz":
            rows = conn.execute(
                _PRAKTYKA_SQL + " WHERE p.uopz_id = ? ORDER BY p.created_at DESC", (user.id,)
            ).fetchall()
        elif user.role == "zopz":
            rows = conn.execute(
                _PRAKTYKA_SQL + " WHERE zo.id = ? ORDER BY p.created_at DESC", (user.id,)
            ).fetchall()
        else:
            rows = []
        return [_enrich_praktyka(r, user, conn) for r in rows]


def get_praktyka_for_student(student_id, user):
    with get_db_connection() as conn:
        rows = conn.execute(
            _PRAKTYKA_SQL + " WHERE p.student_id = ? ORDER BY p.created_at DESC LIMIT 1",
            (student_id,),
        ).fetchall()
        return _enrich_praktyka(rows[0], user, conn) if rows else None


def get_praktyka_by_id(praktyka_id, user):
    with get_db_connection() as conn:
        rows = conn.execute(
            _PRAKTYKA_SQL + " WHERE p.id = ?", (praktyka_id,)
        ).fetchall()
        return _enrich_praktyka(rows[0], user, conn) if rows else None


# ── Document authorization & parsing ──────────────────────────────────────────

# Signature field that "locks" each (typ, role) combination
_USER_SIG_FIELDS = {
    ("zal1",   "dyrektor"): "podpis_uczelnia",
    ("zal1",   "zopz"):     "podpis_zaklad",
    ("zal2",   "dyrektor"): "podpis_dyrektora",
    ("zal2",   "zopz"):     "podpis_zakladu",
    ("zal2a",  "zopz"):     "podpis_zopz",
    ("zal2a",  "student"):  "podpis_student",
    ("zal2a",  "uopz"):     "podpis_uopz",
    ("zal3_1", "dyrektor"): "podpis_dyrektor",
    ("zal3_3", "zopz"):     "podpis_zopz",
    ("zal3_4", "zopz"):     "podpis_zopz",
    ("zal3_5", "uopz"):     "podpis_uopz",
    ("zal3_6", "uopz"):     "podpis_uopz",
    ("zal4",   "zopz"):     "podpis_zopz",
    ("zal4",   "uopz"):     "podpis_uopz",
    ("zal7",   "student"):  "podpis_student",
    ("zal8",   "dyrektor"): "podpis_dyrektor",
}


def can_edit_dok(typ, p, user, dok_data=None):
    """Return True if user may edit/sign this document.

    Pass dok_data (existing JSON dict) to also check whether the user
    has already signed their part - in which case editing is blocked.
    """
    if typ in ("zal1", "zal2"):
        has_access = user.role == "dyrektor" or (user.role == "zopz" and user.id == p["zopz_id"])
    elif typ in ("zal3_1", "zal8"):
        has_access = user.role == "dyrektor"
    elif typ == "zal2a":
        has_access = (
            (user.role == "zopz" and user.id == p["zopz_id"])
            or (user.role == "student" and user.id == p["student_id"])
            or (user.role == "uopz" and user.id == p["uopz_id"])
        )
    elif typ in ("zal3_2", "zal3_3", "zal3_4"):
        has_access = user.role == "zopz" and user.id == p["zopz_id"]
    elif typ in ("zal3_5", "zal3_6"):
        has_access = user.role == "uopz" and user.id == p["uopz_id"]
    elif typ == "zal4":
        has_access = (user.role == "zopz" and user.id == p["zopz_id"]) or (
            user.role == "uopz" and user.id == p["uopz_id"]
        )
    elif typ in ("zal5", "zal7"):
        has_access = user.role == "student" and user.id == p["student_id"]
    else:
        has_access = False

    if not has_access:
        return False

    if dok_data:
        if typ == "zal3_2" and user.role == "zopz":
            # Both ZOPZ signatures present → fully locked
            if dok_data.get("podpis_zopz_1") and dok_data.get("podpis_zopz_2"):
                return False
        else:
            sig = _USER_SIG_FIELDS.get((typ, user.role))
            if sig and dok_data.get(sig):
                return False

    return True


def _merge_sig(result, form, field):
    """Copy signature field from form into result only if non-empty."""
    val = form.get(field, "")
    if isinstance(val, str):
        val = val.strip()
    else:
        val = ""
    if val:
        result[field] = val


def parse_dok(typ, form, existing, user):
    """Parse form/dict data into the JSON payload for a given document type.

    `form` may be a Flask ImmutableMultiDict or a plain dict.
    `existing` is the previously stored dict (may be empty).
    `user` is the acting user (needed for role-split updates).
    """
    def s(key):
        val = form.get(key, "")
        return val.strip() if isinstance(val, str) else (val or "")

    result = dict(existing) if existing else {}

    if typ == "zal1":
        if user.role == "zopz":
            result.update({
                "repr_zakladu":      s("repr_zakladu"),
                "stanowisko_zakladu": s("stanowisko_zakladu"),
            })
            _merge_sig(result, form, "podpis_zaklad")
        elif user.role == "dyrektor":
            result.update({
                "numer":              s("numer"),
                "repr_uczelni":       s("repr_uczelni"),
                "stanowisko_uczelni": s("stanowisko_uczelni"),
            })
            sig_val = (form.get("podpis_uczelnia") or "").strip()
            if sig_val:
                result["podpis_uczelnia"] = sig_val
                if not result.get("data"):
                    from datetime import date as _date
                    result["data"] = _date.today().isoformat()
        return result

    if typ == "zal2":
        if user.role == "dyrektor":
            _merge_sig(result, form, "podpis_dyrektora")
        elif user.role == "zopz":
            _merge_sig(result, form, "podpis_zakladu")
        return result

    if typ == "zal2a":
        if user.role == "zopz":
            efekty = [{"nr": f"{i:02d}", "dzial_czynnosci": s(f"ef_{i:02d}")} for i in range(1, 14)]
            harmonogram = []
            for i in range(1, 51):
                dzial_val = form.get(f"harm_dzial_{i}")
                if dzial_val is None:
                    break
                harmonogram.append({
                    "dzial": dzial_val.strip() if isinstance(dzial_val, str) else "",
                    "dni": s(f"harm_dni_{i}"),
                })
            result.update({"efekty": efekty, "harmonogram": harmonogram})
            _merge_sig(result, form, "podpis_zopz")
        elif user.role == "student":
            _merge_sig(result, form, "podpis_student")
        elif user.role == "uopz":
            sig_val = (form.get("podpis_uopz") or "").strip()
            if sig_val:
                result["podpis_uopz"] = sig_val
                if not result.get("data_uzgodnienia"):
                    from datetime import date as _date
                    result["data_uzgodnienia"] = _date.today().isoformat()
        return result

    if typ == "zal3_1":
        result.update({
            "nr_porozumienia":  s("nr_porozumienia"),
            "data_porozumienia": s("data_porozumienia"),
            "tryb_studiow":     s("tryb_studiow"),
        })
        sig_val = (form.get("podpis_dyrektor") or "").strip()
        if sig_val:
            result["podpis_dyrektor"] = sig_val
            if not result.get("data_skierowania"):
                from datetime import date as _date
                result["data_skierowania"] = _date.today().isoformat()
        return result

    if typ == "zal3_2":
        result.update({
            "stanowisko_zopz": s("stanowisko_zopz"),
            "funkcja_zopz": s("funkcja_zopz"),
        })
        _merge_sig(result, form, "podpis_zopz_1")
        _merge_sig(result, form, "podpis_zopz_2")
        return result

    if typ == "zal3_3":
        result.update({"uwagi": s("uwagi")})
        _merge_sig(result, form, "podpis_zopz")
        return result

    if typ == "zal3_4":
        result.update({"ocena_param": s("ocena_param"), "ocena_opisowa": s("ocena_opisowa")})
        _merge_sig(result, form, "podpis_zopz")
        return result

    if typ == "zal3_5":
        result.update({"ocena_param": s("ocena_param"), "ocena_opisowa": s("ocena_opisowa")})
        _merge_sig(result, form, "podpis_uopz")
        return result

    if typ == "zal3_6":
        result.update({"ocena": s("ocena")})
        _merge_sig(result, form, "podpis_uopz")
        return result

    if typ == "zal4":
        if user.role == "zopz":
            ef_keys = form.getlist("ef") if hasattr(form, "getlist") else form.get("ef", [])
            result.update({
                "liczba_godzin": s("liczba_godzin"),
                "efekty": {
                    f"{i:02d}": (f"{i:02d}" in ef_keys or form.get(f"ef_{i:02d}") == "1")
                    for i in range(1, 14)
                },
            })
            _merge_sig(result, form, "podpis_zopz")
        elif user.role == "uopz":
            result.update({"opinia_uopz": s("opinia_uopz")})
            _merge_sig(result, form, "podpis_uopz")
        return result

    if typ == "zal5":
        return {
            "pytania": {str(i): s(f"p{i}") for i in range(1, 15)},
            "rok_akademicki": s("rok_akademicki"),
            "forma_studiow": s("forma_studiow"),
            "semestr": s("semestr"),
            "liczba_godzin": s("liczba_godzin"),
            "dodatkowe_uwagi": s("dodatkowe_uwagi"),
        }

    if typ == "zal7":
        result.update({
            "charakterystyka": s("charakterystyka"),
            "opis_prac": s("opis_prac"),
            "wiedza_umiejetnosci": s("wiedza_umiejetnosci"),
        })
        _merge_sig(result, form, "podpis_student")
        return result

    if typ == "zal8":
        result.update({
            "data_zaliczenia": s("data_zaliczenia"),
            "sklad_komisji": [s(f"komisja_{i}") for i in range(1, 5)],
            "mini_zadania": [
                {"pytanie": s(f"pytanie_{i}"), "ocena": s(f"mini_{i}")} for i in range(1, 4)
            ],
            "ocena_S": s("ocena_S"), "ocena_U": s("ocena_U"), "ocena_Z": s("ocena_Z"),
        })
        _merge_sig(result, form, "podpis_dyrektor")
        return result

    return result


# ── Database initialisation ────────────────────────────────────────────────────

def init_db():
    with get_db_connection() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS uzytkownik (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imie VARCHAR(64) NOT NULL, nazwisko VARCHAR(64) NOT NULL,
                email VARCHAR(128) NOT NULL UNIQUE, haslo_hash VARCHAR(256) NOT NULL,
                rola VARCHAR(16) NOT NULL CHECK (rola IN ('student','uopz','zopz','dyrektor')),
                aktywny BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
        cols = [r[1] for r in c.execute("PRAGMA table_info(uzytkownik)").fetchall()]
        if "aktywny" not in cols:
            c.execute("ALTER TABLE uzytkownik ADD COLUMN aktywny BOOLEAN NOT NULL DEFAULT 1")
        if "haslo_hash" not in cols:
            c.execute("ALTER TABLE uzytkownik ADD COLUMN haslo_hash VARCHAR(256) NOT NULL DEFAULT ''")

        c.execute("""
            CREATE TABLE IF NOT EXISTS zaklad (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nazwa VARCHAR(256) NOT NULL, adres VARCHAR(256) NOT NULL,
                nip VARCHAR(10) UNIQUE, zopz_id INTEGER NOT NULL REFERENCES uzytkownik(id),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
        z_cols = [r[1] for r in c.execute("PRAGMA table_info(zaklad)").fetchall()]
        if "zopz_id" not in z_cols:
            c.execute("ALTER TABLE zaklad ADD COLUMN zopz_id INTEGER NOT NULL DEFAULT 0")

        c.execute("""
            CREATE TABLE IF NOT EXISTS wpis_dziennika (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                praktyka_id INTEGER NOT NULL REFERENCES praktyka(id),
                numer_dnia INTEGER NOT NULL, data_wpisu DATE NOT NULL,
                opis_prac TEXT NOT NULL, nr_efektow TEXT NOT NULL DEFAULT '[]',
                osoba_nadzorujaca VARCHAR(128),
                potwierdzony BOOLEAN NOT NULL DEFAULT 0, potwierdzone_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(praktyka_id, numer_dnia)
            )""")

        _DOK_CHECK = (
            "'zal1','zal2','zal2a','zal3_1','zal3_2','zal3_3',"
            "'zal3_4','zal3_5','zal3_6','zal4','zal5','zal7','zal8'"
        )
        _dok = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='dokument'").fetchone()
        if _dok is None:
            c.execute(f"""
                CREATE TABLE dokument (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    praktyka_id INTEGER NOT NULL REFERENCES praktyka(id),
                    typ VARCHAR(16) NOT NULL CHECK (typ IN ({_DOK_CHECK})),
                    zawartosc_json TEXT NOT NULL DEFAULT '{{}}',
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(praktyka_id, typ)
                )""")
        elif "zal5" not in (_dok["sql"] or ""):
            c.execute("ALTER TABLE dokument RENAME TO _dokument_bak")
            c.execute(f"""
                CREATE TABLE dokument (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    praktyka_id INTEGER NOT NULL REFERENCES praktyka(id),
                    typ VARCHAR(16) NOT NULL CHECK (typ IN ({_DOK_CHECK})),
                    zawartosc_json TEXT NOT NULL DEFAULT '{{}}',
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(praktyka_id, typ)
                )""")
            c.execute("INSERT INTO dokument SELECT id,praktyka_id,typ,zawartosc_json,updated_at FROM _dokument_bak")
            c.execute("DROP TABLE _dokument_bak")

        c.execute("""
            CREATE TABLE IF NOT EXISTS praktyka (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES uzytkownik(id),
                uopz_id INTEGER NOT NULL REFERENCES uzytkownik(id),
                zaklad_id INTEGER NOT NULL REFERENCES zaklad(id),
                data_rozpoczecia DATE NOT NULL, data_zakonczenia DATE NOT NULL,
                etap VARCHAR(32) NOT NULL DEFAULT 'dyrektor_wysyla_wstepne',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

        c.execute("UPDATE praktyka SET etap='dziennik_aktywny' WHERE etap='w_trakcie'")
