```mermaid
flowchart TD
    A([Użytkownik otwiera załącznik]) --> B{Czy użytkownik\njest zalogowany?}

    B -- Nie --> C[Przekieruj na\nstronę logowania]
    C --> KONIEC1([Koniec])

    B -- Tak --> G{"Czy użytkownik jest\nuczestnikiem praktyki?\nstudent / uopz / zopz / dyrektor"}
    G -- Nie --> X[403 Forbidden]
    X --> KONIEC0([Koniec])

    G -- Tak --> D{Czy rola ma prawo\nedycji tego typu\nzałącznika?}
    D -- Nie --> E[Podgląd Read-only]

    D -- Tak --> F{Czy ta rola\nzłożyła już swój\npodpis?}
    F -- Tak --> E
    F -- Nie --> H[Udostępnij formularz edycji\n+ przycisk „Podpisz”]

    H --> I{Akcja użytkownika}
    I -- Zapis --> J[Walidacja w backendzie\nparse_dok – tylko pola tej roli]
    I -- Podpis --> K[Potwierdzenie w UI\n+ zapis podpisu]
    I -- Anuluj --> KONIEC2([Wróć])

    J --> N[Zapis do dokument.zawartosc_json]
    K --> N
    N --> O[_try_auto_advance:\nczy wszystkie podpisy etapu złożone?]
    O -- Tak --> P[Zmiana etapu praktyki]
    O -- Nie --> Q[Pozostań na etapie]
    P --> KONIEC3([Koniec – zapisano])
    Q --> KONIEC3

    E --> KONIEC4([Koniec – tryb podglądu])

    style H fill:#1D9E75,color:#fff
    style E fill:#888780,color:#fff
    style C fill:#E24B4A,color:#fff
    style X fill:#E24B4A,color:#fff
```

## Uwagi

- Uprawnienia wyznacza funkcja **`can_edit_dok(typ, praktyka, user, dok_data)`** w `api/db.py`:
  sprawdza udział w praktyce, dopasowanie roli do typu załącznika oraz to, czy rola już
  podpisała (po podpisie część dokumentu jest trwale zablokowana).
- Zapis przechodzi przez **`parse_dok()`**, który aktualizuje wyłącznie pola należące do roli
  bieżącego użytkownika (np. ZOPZ wypełnia efekty zał4, UOPZ – opinię).
- Po każdym zapisie sprawdzane jest, czy etap praktyki może zmienić się automatycznie.
```
