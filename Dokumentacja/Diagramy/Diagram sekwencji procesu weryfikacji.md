```mermaid
sequenceDiagram
    participant S as Student
    participant B as Backend Flask (api/routes.py)
    participant DB as SQLite (data/app.db)
    participant Z as ZOPZ

    Note over S,Z: Prowadzenie dziennika praktyki (120 dni)

    S->>B: POST /api/praktyki/{id}/dziennik {data, opis, nr_efektow}
    B->>B: Walidacja (data_wpisu, opis_prac wymagane)
    alt Dane niekompletne
        B-->>S: 400 {ok:false, error}
    else Dane poprawne
        B->>DB: INSERT wpis_dziennika (numer_dnia = kolejny)
        DB-->>B: OK
        B-->>S: 201 {ok:true, numer_dnia}
    end

    Note over Z,DB: Zatwierdzanie strony (10 wpisów)

    Z->>B: POST /api/praktyki/{id}/dziennik/strony/{n}/zatwierdz
    B->>B: Sprawdź rolę = ZOPZ zakładu
    alt Strona ma mniej niż 10 wpisów
        B-->>Z: 409 {error: za mało wpisów}
    else Strona kompletna
        B->>DB: UPDATE potwierdzony=1, potwierdzone_at dla dni strony n
        DB-->>B: OK
        alt Wszystkie 120 wpisów potwierdzone
            B->>DB: UPDATE praktyka SET etap='zal7_do_podpisania'
            B-->>Z: 200 {advanced:true}
        else
            B-->>Z: 200 {confirmed_total}
        end
    end
```

## Uwagi

- Dane przechowywane są w **SQLite** (`data/app.db`), nie w plikach JSON.
- Dziennik liczy **120 wpisów** pogrupowanych w **12 stron po 10 dni**; ZOPZ zatwierdza
  całą stronę naraz (podpis ZOPZ pojawia się na zatwierdzonej stronie PDF).
- Po potwierdzeniu wszystkich 120 wpisów etap praktyki przechodzi automatycznie do
  `zal7_do_podpisania` (mechanizm także samonaprawiający przy wczytaniu praktyki).
- Stronę niezatwierdzoną student może jeszcze edytować
  (`PUT /api/praktyki/{id}/dziennik/{numer}`).
```
