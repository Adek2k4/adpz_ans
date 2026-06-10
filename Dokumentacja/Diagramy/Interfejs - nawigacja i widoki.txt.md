```mermaid
flowchart TD
    START([Wejście na stronę]) --> NAV[Nawigacja: Start / Panel / Kontakt / Admin]
    NAV --> AUTH{Zalogowany?}

    AUTH -- Nie --> LOGIN[/login – e-mail+hasło\nlub logowanie Microsoft/]
    LOGIN --> CRED{Dane poprawne?}
    CRED -- Nie --> ERR1[Błąd logowania]
    ERR1 --> LOGIN
    CRED -- Tak --> ROLE{Rola?}

    AUTH -- Tak --> ROLE

    ROLE -- Student --> DS[Panel studenta]
    ROLE -- UOPZ --> DU[Panel UOPZ]
    ROLE -- ZOPZ --> DZ[Panel ZOPZ]
    ROLE -- Dyrektor --> DD[Panel dyrektora]

    DS --> DS1[Moja praktyka + status etapu]
    DS --> DS2[Moje dane: nr albumu, specjalność]
    DS --> DS3[Załączniki do podpisu]
    DS --> DS4[Dziennik praktyki]

    DU --> DU1[Utwórz praktykę]
    DU --> DU2[Lista praktyk + załączniki]
    DU --> DU3[Zamknięcie praktyki]

    DZ --> DZ1[Praktyki zakładu + załączniki]
    DZ --> DZ2[Zatwierdzanie stron dziennika]

    DD --> DD1[Praktyki + załączniki do podpisu]
    DD --> DD2[/zatwierdzanie – aktywacja kont ZOPZ/]

    DS1 --> DOC[Widok załącznika\n/praktyka/id/dokument/typ]
    DU2 --> DOC
    DZ1 --> DOC
    DD1 --> DOC
    DOC --> EDIT{can_edit_dok?}
    EDIT -- Tak --> FORM[Formularz + Podpisz + Pobierz PDF]
    EDIT -- Nie --> READONLY[Podgląd Read-only + Pobierz PDF]

    NAV --> ADMIN[/admin – panel chroniony hasłem/]
    ADMIN --> ADMINP[Zarządzanie rolami\n+ zmiana hasła panelu]

    style LOGIN fill:#378ADD,color:#fff
    style ERR1 fill:#E24B4A,color:#fff
    style FORM fill:#1D9E75,color:#fff
    style READONLY fill:#888780,color:#fff
    style ADMIN fill:#6A4FB6,color:#fff
```

## Uwagi

- Pasek nawigacji (`base.html`): **Start, Panel, Kontakt, Admin** oraz – po zalogowaniu –
  **Profil, Wyloguj** (a dla dyrektora dodatkowo **Zatwierdzanie**). W trybie demo dostępny
  jest też dropdown **🛠 DEV** z szybkim logowaniem na konta testowe.
- Panel (`/dashboard`) renderuje się zależnie od roli (jeden szablon `dashboard.html`).
- Załączniki obsługiwane są jednym widokiem `dokument.html` (gałąź `if/elif` per typ),
  z możliwością pobrania PDF.
- Panel administratora (`/admin`) jest niezależny od kont użytkowników – chroniony samym hasłem.
```
