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

## Struktura

- app.py
- requirements.txt
- .env.example
- templates/
- static/styles.css
- data/submissions.json
- data/app.db (tworzony automatycznie)
