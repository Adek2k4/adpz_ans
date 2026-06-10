Aplikacja prowadzi praktykę przez **13-etapowy workflow** zapisany w polu `praktyka.etap`.
Etap zmienia się **automatycznie** po złożeniu wszystkich wymaganych podpisów na danym etapie
(`_try_auto_advance` w `api/routes.py`).

```mermaid
flowchart TD
    A([UOPZ tworzy praktykę]) --> E0[etap: dyrektor_wysyla_wstepne]

    E0 -->|Dyrektor i ZOPZ podpisują zał1 i zał2| E2[etap: zopz_wypelnia_zal2a]
    E2 -->|ZOPZ wypełnia efekty + harmonogram, podpisuje zał2a| E3[etap: student_podpisuje_zal2a]
    E3 -->|Student podpisuje zał2a| E4[etap: uopz_podpisuje_zal2a]
    E4 -->|UOPZ podpisuje zał2a| E5[etap: dyrektor_wysyla_zal3_1]
    E4 -->|UOPZ odrzuca| E2
    E5 -->|Dyrektor wystawia skierowanie zał3.1| E6[etap: zopz_podpisuje_zal3_2]
    E6 -->|ZOPZ zatwierdza szkolenie BHP zał3.2| E7[etap: dziennik_aktywny]

    E7 --> D1[Student dodaje wpisy dziennika]
    D1 --> D2{Wpis zawiera\nopis i datę?}
    D2 -- Nie --> D3[400 – wymagane pola]
    D3 --> D1
    D2 -- Tak --> D4[Zapis wpisu]
    D4 --> D5[ZOPZ zatwierdza stronę 10 wpisów]
    D5 --> D6{120 wpisów\npotwierdzonych?}
    D6 -- Nie --> D1
    D6 -- Tak --> E8[etap: zal7_do_podpisania]

    E8 -->|Student składa sprawozdanie zał7| E9[etap: dokumenty_koncowe]
    E9 -->|ZOPZ: zał3.3, 3.4, zał4 efekty; UOPZ: zał3.5, 3.6, zał4 opinia; Student: zał5| E10[etap: dyrektor_podpisuje_zal8]
    E10 -->|Dyrektor podpisuje protokół zał8\nK = 0.4·E + 0.1·S + 0.2·U + 0.3·Z| E11[etap: uopz_zamyka]
    E11 -->|UOPZ zamyka praktykę| E12([etap: zamknieta])

    style E12 fill:#1D9E75,color:#fff
    style D3 fill:#E24B4A,color:#fff
```

## Uwagi

- **Tworzenie praktyki** – tylko UOPZ; wskazuje studenta, zakład (z opiekunem ZOPZ) i termin.
- **Dane studenta** (numer albumu, specjalność) uzupełnia student w panelu; trafiają
  automatycznie do załączników 2a/3.1/4/7 i dziennika.
- **Ocena końcowa** liczona jest w protokole **zał8** (`K = 0,4·E + 0,1·S + 0,2·U + 0,3·Z`),
  gdzie S/U/Z pochodzą z ocen w załącznikach 3.4–3.6, a E ze średniej mini-zadań.
- W projekcie **nie ma** osobnej ścieżki „praca/staż” (zał4a/4b), hospitacji ani integracji
  z USOS – to elementy regulaminu papierowego, nie zaimplementowane w aplikacji.
```
