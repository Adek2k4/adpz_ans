```mermaid
stateDiagram-v2
    [*] --> Pusty : Załącznik dostępny na danym etapie praktyki

    Pusty --> Wypelniany : Uprawniona rola otwiera formularz
    Wypelniany --> Wypelniany : Zapis wersji roboczej (PUT dokumentu)

    Wypelniany --> Podpisany : Rola składa podpis\n("Podpisano (data) + imię i nazwisko")

    Podpisany --> [*] : Część roli trwale zablokowana

    note right of Pusty
        Treść załącznika przechowywana jest jako
        JSON w dokument.zawartosc_json (jeden wiersz
        na parę praktyka + typ).
    end note

    note right of Wypelniany
        Niektóre załączniki wypełnia kilka ról kolejno,
        np. zał2a: ZOPZ → Student → UOPZ,
        zał1: ZOPZ (strona zakładu) → Dyrektor (strona uczelni).
    end note

    note right of Podpisany
        Po podpisie can_edit_dok() blokuje edycję dla danej roli.
        Gdy wszystkie wymagane podpisy są złożone, etap praktyki
        zmienia się automatycznie (_try_auto_advance).
    end note
```

## Uwagi

- Dokument **nie ma osobnej kolumny statusu** – stan wynika z obecności podpisów
  w `zawartosc_json` oraz z bieżącego `etap` praktyki.
- Lista typów: `zal1`, `zal2`, `zal2a`, `zal3_1`..`zal3_6`, `zal4`, `zal5`, `zal7`, `zal8`.
- Każdy załącznik można pobrać jako PDF (`GET /api/praktyki/<id>/dokumenty/<typ>/pdf`).
```
