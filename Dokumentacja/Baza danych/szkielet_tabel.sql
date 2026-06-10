-- Schemat bazy danych (SQLite) – odpowiada init_db() w api/db.py
-- Baza tworzona jest automatycznie przy starcie aplikacji (data/app.db).

CREATE TABLE uzytkownik (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    imie        VARCHAR(64)  NOT NULL,
    nazwisko    VARCHAR(64)  NOT NULL,
    email       VARCHAR(128) NOT NULL UNIQUE,
    haslo_hash  VARCHAR(256) NOT NULL,           -- puste dla kont Microsoft (OAuth)
    rola        VARCHAR(16)  NOT NULL CHECK (rola IN ('student','uopz','zopz','dyrektor')),
    aktywny     BOOLEAN      NOT NULL DEFAULT 1,  -- konta lokalne ZOPZ czekają na zatwierdzenie
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE zaklad (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    nazwa       VARCHAR(256) NOT NULL,
    adres       VARCHAR(256) NOT NULL,
    nip         VARCHAR(10)  UNIQUE,
    zopz_id     INTEGER      NOT NULL REFERENCES uzytkownik(id),  -- opiekun zakładowy
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE praktyka (
    id                INTEGER      PRIMARY KEY AUTOINCREMENT,
    student_id        INTEGER      NOT NULL REFERENCES uzytkownik(id),
    uopz_id           INTEGER      NOT NULL REFERENCES uzytkownik(id),
    zaklad_id         INTEGER      NOT NULL REFERENCES zaklad(id),
    data_rozpoczecia  DATE         NOT NULL,
    data_zakonczenia  DATE         NOT NULL,
    etap              VARCHAR(32)  NOT NULL DEFAULT 'dyrektor_wysyla_wstepne',  -- stan workflow (13 etapów)
    nr_albumu         VARCHAR(16)  NOT NULL DEFAULT '',   -- uzupełniane przez studenta
    specjalnosc       VARCHAR(128) NOT NULL DEFAULT '',   -- uzupełniane przez studenta
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wpis_dziennika (
    id                INTEGER      PRIMARY KEY AUTOINCREMENT,
    praktyka_id       INTEGER      NOT NULL REFERENCES praktyka(id),
    numer_dnia        INTEGER      NOT NULL,            -- 1..120
    data_wpisu        DATE         NOT NULL,
    opis_prac         TEXT         NOT NULL,
    nr_efektow        TEXT         NOT NULL DEFAULT '[]',  -- JSON: lista kodów efektów (np. ["01","05"])
    osoba_nadzorujaca VARCHAR(128),                     -- zachowane w schemacie, nieużywane w UI
    potwierdzony      BOOLEAN      NOT NULL DEFAULT 0,   -- strona zatwierdzona przez ZOPZ
    potwierdzone_at   DATETIME,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (praktyka_id, numer_dnia)
);

CREATE TABLE dokument (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER      NOT NULL REFERENCES praktyka(id),
    typ             VARCHAR(16)  NOT NULL CHECK (typ IN (
                        'zal1','zal2','zal2a','zal3_1','zal3_2','zal3_3',
                        'zal3_4','zal3_5','zal3_6','zal4','zal5','zal7','zal8'
                    )),
    zawartosc_json  TEXT         NOT NULL DEFAULT '{}',  -- pola formularza i podpisy załącznika
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (praktyka_id, typ)
);

CREATE TABLE app_setting (
    klucz    VARCHAR(64) PRIMARY KEY,   -- np. 'admin_password_hash'
    wartosc  TEXT        NOT NULL DEFAULT ''
);

-- Uwagi:
-- * Lista 13 efektów uczenia się (E01–E13) nie jest tabelą – to stała EFEKTY_UCZENIA w api/db.py.
-- * Treść każdego załącznika (pola i podpisy) trzymana jest jako JSON w dokument.zawartosc_json.
-- * Administrator nie jest kontem użytkownika – panel /admin chroniony jest hasłem,
--   którego hash przechowuje app_setting (klucz 'admin_password_hash').
