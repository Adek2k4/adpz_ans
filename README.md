# System obsługi praktyk zawodowych – ANS Elbląg

Aplikacja Flask do zarządzania praktykami zawodowymi na kierunku Informatyka w Akademii Nauk Stosowanych w Elblągu. Obsługuje pełny cykl życia praktyki: od podpisania porozumienia, przez dziennik praktyk, aż po protokół zaliczenia.

## Wymagania

- Python 3.10+
- Flask, Flask-Login, Authlib, python-dotenv, werkzeug

## Uruchomienie

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # uzupełnij dane
python app.py
```

Aplikacja dostępna pod: http://127.0.0.1:5000

## Konfiguracja (.env)

```
FLASK_SECRET_KEY=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://127.0.0.1:5000/auth/callback
DIRECTOR_EMAIL=dyrektor@uczelnia.pl
```

Logowanie lokalne (bez Azure AD) dostępne przez `/register` i `/login`.

## Role użytkowników

| Rola | Opis |
|------|------|
| `student` | Podpisuje dokumenty, prowadzi dziennik, składa sprawozdanie |
| `uopz` | Uczelniany Opiekun Praktyki – tworzy praktyki, podpisuje dokumenty, zamyka praktykę |
| `zopz` | Zakładowy Opiekun Praktyki – podpisuje dokumenty, zatwierdza strony dziennika |
| `dyrektor` | Podpisuje porozumienie, skierowanie i protokół zaliczenia; zatwierdza konta |

## Workflow praktyki (13 etapów)

Etap zmienia się **automatycznie** po podpisaniu wszystkich wymaganych dokumentów.

```
dyrektor_wysyla_wstepne   → ZOPZ i Dyrektor podpisują zał1 i zał2
zopz_podpisuje_wstepne    → (przeskakiwany automatycznie gdy oba podpisy już złożone)
zopz_wypelnia_zal2a       → ZOPZ wypełnia efekty i harmonogram, podpisuje zał2a
student_podpisuje_zal2a   → Student podpisuje zał2a
uopz_podpisuje_zal2a      → UOPZ podpisuje zał2a (może odrzucić do ZOPZu)
dyrektor_wysyla_zal3_1    → Dyrektor wystawia skierowanie (zał3.1)
zopz_podpisuje_zal3_2     → ZOPZ zatwierdza szkolenie BHP (zał3.2)
dziennik_aktywny          → Student prowadzi dziennik (120 wpisów × 10 stron)
zal7_do_podpisania        → Student składa sprawozdanie (zał7)
dokumenty_koncowe         → ZOPZ/UOPZ wypełniają zał3.3–3.6, zał4, student zał5
dyrektor_podpisuje_zal8   → Dyrektor podpisuje protokół zaliczenia (zał8)
uopz_zamyka               → UOPZ zamyka praktykę
zamknieta                 → Praktyka zakończona
```

## Dokumenty (załączniki)

| Symbol | Nazwa | Kto wypełnia |
|--------|-------|-------------|
| zał1 | Porozumienie z zakładem pracy | ZOPZ (strona zakładu) + Dyrektor (strona uczelni) |
| zał2 | Program praktyki | ZOPZ + Dyrektor (podpisy) |
| zał2a | Program i harmonogram | ZOPZ (efekty, harmonogram) → Student → UOPZ |
| zał3.1 | Skierowanie na praktykę | Dyrektor |
| zał3.2 | Szkolenie BHP | ZOPZ (dwa podpisy) |
| zał3.3 | Zaświadczenie odbycia praktyki | ZOPZ |
| zał3.4 | Ocena przebiegu praktyki (zakład) | ZOPZ |
| zał3.5 | Ocena przebiegu praktyki (uczelnia) | UOPZ |
| zał3.6 | Ocena sprawozdania | UOPZ |
| zał4 | Potwierdzenie efektów uczenia się | ZOPZ (efekty) + UOPZ (opinia) |
| zał5 | Kwestionariusz ankiety | Student |
| zał7 | Sprawozdanie studenta | Student |
| zał8 | Protokół zaliczenia praktyki | Dyrektor |

Po podpisaniu dokumentu jego edycja jest **trwale zablokowana** dla danej roli.

## REST API

Wszystkie odpowiedzi mają format `{"ok": true, "data": {...}}` lub `{"ok": false, "error": "..."}`.

### Praktyki

| Metoda | URL | Opis |
|--------|-----|------|
| GET | `/api/praktyki` | Lista praktyk (filtrowana per rola) |
| POST | `/api/praktyki` | Utwórz praktykę (UOPZ) |
| GET | `/api/praktyki/<id>` | Szczegóły praktyki |

### Dziennik

| Metoda | URL | Opis |
|--------|-----|------|
| GET | `/api/praktyki/<id>/dziennik` | Lista wpisów + strony |
| POST | `/api/praktyki/<id>/dziennik` | Dodaj wpis (student) |
| PUT | `/api/praktyki/<id>/dziennik/<nr>` | Edytuj wpis (student, strona niezatwierdzona) |
| POST | `/api/praktyki/<id>/dziennik/strony/<n>/zatwierdz` | Zatwierdź stronę (ZOPZ) |

### Dokumenty

| Metoda | URL | Opis |
|--------|-----|------|
| GET | `/api/praktyki/<id>/dokumenty/<typ>` | Pobierz dokument |
| PUT | `/api/praktyki/<id>/dokumenty/<typ>` | Zapisz / podpisz dokument |

Po każdym zapisie sprawdzane jest czy etap praktyki może się automatycznie zmienić.

### Dane referencyjne

| Metoda | URL | Opis |
|--------|-----|------|
| GET | `/api/zaklady` | Lista zakładów pracy |
| GET | `/api/uzytkownicy?rola=student` | Lista użytkowników |
| GET | `/api/me` | Dane zalogowanego użytkownika |

## Struktura projektu

```
app.py                  # Auth, renderowanie szablonów, konta demo
api/
  __init__.py
  db.py                 # Stałe, helpery DB, init_db(), can_edit_dok(), parse_dok()
  routes.py             # Blueprint REST API
static/
  styles.css
  js/api.js             # apiCall(), submitForm(), flashSuccess()
templates/
  base.html
  dashboard.html        # Panel główny (role-based)
  dokument.html         # Wszystkie załączniki (1 plik, if/elif per typ)
  dziennik.html         # Dziennik 120 wpisów / 12 stron
  login.html
  profil.html
  approvals.html
data/
  app.db                # SQLite (tworzony automatycznie)
```

## Baza danych (SQLite)

```sql
uzytkownik  (id, imie, nazwisko, email, haslo_hash, rola, aktywny)
zaklad      (id, nazwa, adres, nip, zopz_id)
praktyka    (id, student_id, uopz_id, zaklad_id, data_rozpoczecia, data_zakonczenia, etap)
dokument    (id, praktyka_id, typ, zawartosc_json, updated_at)
wpis_dziennika (id, praktyka_id, numer_dnia, data_wpisu, opis_prac, nr_efektow,
                osoba_nadzorujaca, potwierdzony, potwierdzone_at)
```

## Konta demonstracyjne

Przy starcie aplikacji tworzone są automatycznie konta do prezentacji. Dostępne przez dropdown **🛠 DEV** w nawigacji:

| Email | Rola |
|-------|------|
| student1@dev.local | student |
| student2@dev.local | student |
| student3@dev.local | student |
| zopz@dev.local | zopz |
| uopz@dev.local | uopz |
| dyrektor@dev.local | dyrektor |

Na stronie dziennika (zalogowany jako student) dostępny jest przycisk **🛠 DEV: Wypełnij cały dziennik** do szybkiego wypełnienia 120 wpisów testowych.
