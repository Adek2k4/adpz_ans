```mermaid
erDiagram
    UZYTKOWNIK {
        int id PK
        string imie
        string nazwisko
        string email UK
        string haslo_hash
        string rola "student|uopz|zopz|dyrektor"
        bool aktywny
        datetime created_at
    }

    ZAKLAD {
        int id PK
        string nazwa
        string adres
        string nip UK
        int zopz_id FK
        datetime created_at
    }

    PRAKTYKA {
        int id PK
        int student_id FK
        int uopz_id FK
        int zaklad_id FK
        date data_rozpoczecia
        date data_zakonczenia
        string etap
        string nr_albumu
        string specjalnosc
        datetime created_at
        datetime updated_at
    }

    WPIS_DZIENNIKA {
        int id PK
        int praktyka_id FK
        int numer_dnia
        date data_wpisu
        text opis_prac
        text nr_efektow "JSON: lista kodów efektów"
        string osoba_nadzorujaca
        bool potwierdzony
        datetime potwierdzone_at
        datetime created_at
    }

    DOKUMENT {
        int id PK
        int praktyka_id FK
        string typ "zal1..zal8"
        text zawartosc_json
        datetime updated_at
    }

    APP_SETTING {
        string klucz PK
        text wartosc
    }

    UZYTKOWNIK ||--o{ PRAKTYKA : "student"
    UZYTKOWNIK ||--o{ PRAKTYKA : "uopz"
    UZYTKOWNIK ||--o{ ZAKLAD : "zopz"
    ZAKLAD     ||--o{ PRAKTYKA : ""
    PRAKTYKA   ||--o{ WPIS_DZIENNIKA : ""
    PRAKTYKA   ||--o{ DOKUMENT : ""
```

## Uwagi

- **Role** użytkownika: `student`, `uopz` (uczelniany opiekun), `zopz` (zakładowy opiekun),
  `dyrektor`. Administrator nie jest kontem użytkownika — to panel `/admin` chroniony hasłem
  (hash w tabeli `APP_SETTING`, klucz `admin_password_hash`).
- **ZAKLAD.zopz_id** wskazuje użytkownika z rolą `zopz`, który jest opiekunem zakładowym.
- **PRAKTYKA.etap** — stan w 13-etapowym workflow (np. `dyrektor_wysyla_wstepne`,
  `dziennik_aktywny`, `zamknieta`); zmienia się automatycznie po podpisaniu dokumentów.
- **DOKUMENT** — jeden wiersz na (praktyka, typ); cała treść załącznika trzymana jest jako
  JSON w `zawartosc_json` (pola formularzy i podpisy). Unikalność: `(praktyka_id, typ)`.
- **WPIS_DZIENNIKA** — 120 wpisów na praktykę (`UNIQUE(praktyka_id, numer_dnia)`),
  grupowane po 10 w strony zatwierdzane przez ZOPZ. `nr_efektow` to lista kodów efektów
  zapisana jako JSON. Kolumna `osoba_nadzorujaca` pozostaje w schemacie, ale nie jest
  już używana w interfejsie.
- **Efekty uczenia się** (E01–E13) nie są osobną tabelą — to stała lista w kodzie
  (`EFEKTY_UCZENIA` w `api/db.py`).
- **APP_SETTING** — ustawienia aplikacji typu klucz/wartość (m.in. hash hasła administratora).
```
