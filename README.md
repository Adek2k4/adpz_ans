# System obslugi praktyk

Prosta aplikacja Flask do obslugi praktyk zawodowych. Zawiera podstawowe strony oraz formularz zwracajacy JSON, zapisujacy dane do pliku i dziennik praktyk z lista wpisow.

## Wymagania

- Python 3.10+
- Flask

## Uruchomienie (Windows PowerShell)

1. Utworz i aktywuj venv:

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Zainstaluj zaleznosci i uruchom aplikacje:

```
pip install Flask
python app.py
```

Aplikacja bedzie dostepna pod http://127.0.0.1:5000

## Najwazniejsze funkcje

- Strona glowna i podstawowe podstrony: /, /kontakt, /hobby
- Formularz: /formularz
  - GET zwraca formularz
  - POST zwraca JSON i zapisuje dane do data/submissions.json
  - Dziennik praktyk jako lista wpisow (data, activity, hours) obslugiwany przez request.form.getlist
  - Dynamiczne dodawanie i usuwanie wierszy (JavaScript)

## Struktura

- app.py
- templates/
- data/submissions.json
