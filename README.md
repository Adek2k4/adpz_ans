# System obslugi praktyk

Prosta aplikacja Flask do obslugi praktyk zawodowych. Zawiera podstawowe strony oraz formularz zwracajacy JSON, zapisujacy dane do pliku i dziennik praktyk z lista wpisow.

## Wymagania

- Python 3.10+
- Flask
- Flask-Login
- Authlib
- python-dotenv

## Uruchomienie (Windows PowerShell)

1. Utworz i aktywuj venv:

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Zainstaluj zaleznosci i uruchom aplikacje:

```
pip install -r requirements.txt
python app.py
```

Aplikacja bedzie dostepna pod http://127.0.0.1:5000

## Konfiguracja logowania Microsoft (OAuth2)

1. Skopiuj plik `.env.example` jako `.env` i uzupelnij dane.
2. Ustaw w Azure AD aplikacje i dodaj redirect URI: `http://127.0.0.1:5000/auth/callback`.
3. Zrestartuj aplikacje.

Zmienne w `.env`:

```
FLASK_SECRET_KEY=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://127.0.0.1:5000/auth/callback
```

## Najwazniejsze funkcje

- Strona glowna i podstawowe podstrony: /, /kontakt, /hobby
- Formularz: /formularz
  - GET zwraca formularz
  - POST zwraca JSON i zapisuje dane do data/submissions.json
  - Dziennik praktyk jako lista wpisow (data, activity, hours) obslugiwany przez request.form.getlist
  - Dynamiczne dodawanie i usuwanie wierszy (JavaScript)
- Logowanie Microsoft (OAuth2) + profil uzytkownika i role
- REST API: /api/students, /api/internships, /api/documents
- Frontend: panel /dashboard z formularzami i lista danych z API

## API (REST)

Endpointy:

- GET /api/students
- POST /api/students
- GET /api/students/<id>
- PUT/PATCH /api/students/<id>
- DELETE /api/students/<id>

- GET /api/internships
- POST /api/internships
- GET /api/internships/<id>
- PUT/PATCH /api/internships/<id>
- DELETE /api/internships/<id>

- GET /api/documents
- POST /api/documents
- GET /api/documents/<id>
- PUT/PATCH /api/documents/<id>
- DELETE /api/documents/<id>

- GET /api/journal-entries
- POST /api/journal-entries
- GET /api/journal-entries/<id>
- PUT/PATCH /api/journal-entries/<id>
- DELETE /api/journal-entries/<id>

- GET /api/effects
- POST /api/effects
- GET /api/effects/<id>
- PUT/PATCH /api/effects/<id>
- DELETE /api/effects/<id>

Filtrowanie:

- /api/internships?student_id=1
- /api/documents?internship_id=1
- /api/journal-entries?internship_id=1
- /api/effects?internship_id=1

## Frontend (panel)

Panel pod adresem `/dashboard` korzysta z REST API i pozwala:

- dodawac studentow
- tworzyc praktyki
- dodawac wpisy dziennika
- przypisywac efekty uczenia

Wszystkie operacje sa wykonywane przez fetch do endpointow API i wyswietlaja komunikaty o bledach.

Przyklady (curl):

```
curl -X POST http://127.0.0.1:5000/api/students \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Jan Kowalski\", \"email\": \"jan@example.com\"}"

curl -X POST http://127.0.0.1:5000/api/internships \
  -H "Content-Type: application/json" \
  -d "{\"student_id\": 1, \"company\": \"Tech Sp. z o.o.\", \"start_date\": \"2026-06-01\", \"end_date\": \"2026-09-30\", \"status\": \"active\"}"

curl -X POST http://127.0.0.1:5000/api/documents \
  -H "Content-Type: application/json" \
  -d "{\"internship_id\": 1, \"type\": \"report\", \"status\": \"draft\", \"notes\": \"Wersja robocza\"}"
```

## Struktura

- app.py
- api/routes.py
- requirements.txt
- .env.example
- templates/
- templates/dashboard.html
- static/styles.css
- static/js/dashboard.js
- data/submissions.json
- data/api_students.json
- data/api_internships.json
- data/api_documents.json
- data/api_journal_entries.json
- data/api_effects.json
- data/app.db (tworzony automatycznie)
