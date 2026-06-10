```mermaid
sequenceDiagram
    participant U as UOPZ
    participant D as Dyrektor
    participant Z as ZOPZ
    participant S as Student

    rect rgb(230, 241, 251)
        Note over U,Z: Dokumenty wstępne (etap: dyrektor_wysyla_wstepne)
        U->>U: Utworzenie praktyki (student, zakład, termin)
        Z->>Z: Podpis zał1 (strona zakładu) i zał2
        D->>D: Podpis zał1 (strona uczelni) i zał2
        Note over Z,D: Po obu podpisach etap przechodzi dalej automatycznie
    end

    rect rgb(225, 245, 238)
        Note over S,U: Program i harmonogram (zał2a)
        Z->>Z: Wypełnia efekty + harmonogram, podpisuje zał2a
        S->>S: Podpisuje zał2a
        U->>U: Podpisuje zał2a (lub odrzuca do ZOPZ)
    end

    rect rgb(250, 238, 218)
        Note over D,Z: Skierowanie i BHP
        D->>S: Skierowanie na praktykę (zał3.1)
        Z->>Z: Zatwierdzenie szkolenia BHP (zał3.2)
    end

    rect rgb(250, 244, 218)
        Note over S,Z: Realizacja – dziennik (etap: dziennik_aktywny)
        loop 120 dni roboczych (12 stron po 10)
            S->>Z: Wpisy w dzienniku
            Z-->>S: Zatwierdzenie strony (podpis ZOPZ)
        end
        Note over S,Z: Po 120 potwierdzonych wpisach etap → zal7
    end

    rect rgb(230, 241, 251)
        Note over S,U: Dokumenty końcowe
        S->>U: Sprawozdanie studenta (zał7)
        Z->>U: zał3.3 zaświadczenie, zał3.4 ocena, zał4 efekty
        U->>U: zał3.5 ocena, zał3.6 ocena sprawozdania, zał4 opinia
        S->>U: Ankieta (zał5)
    end

    rect rgb(238, 237, 254)
        Note over D,U: Protokół i zamknięcie
        D->>D: Protokół zaliczenia (zał8), K = 0.4·E + 0.1·S + 0.2·U + 0.3·Z
        U->>U: Zamknięcie praktyki (etap: zamknieta)
    end
```

## Uwagi

- Diagram odzwierciedla **13-etapowy workflow** z pola `praktyka.etap`; przejścia następują
  automatycznie po złożeniu wymaganych podpisów.
- Oceny składowe: **S** – ocena sprawozdania (zał3.6), **U** – UOPZ (zał3.5),
  **Z** – ZOPZ (zał3.4), **E** – średnia mini-zadań w protokole (zał8).
- Role w aplikacji: student, UOPZ, ZOPZ, dyrektor; konta ZOPZ aktywuje dyrektor
  (`/zatwierdzanie`), a role nadaje administrator (`/admin`).
```
