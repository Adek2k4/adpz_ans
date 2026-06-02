CREATE TABLE uzytkownik (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    imie        VARCHAR(64)  NOT NULL,
    nazwisko    VARCHAR(64)  NOT NULL,
    email       VARCHAR(128) NOT NULL UNIQUE,
    haslo_hash  VARCHAR(256) NOT NULL,
    rola        VARCHAR(16)  NOT NULL CHECK (rola IN ('student','uopz','zopz','dyrektor')),
    aktywny     BOOLEAN      NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE zaklad (
    id                   INTEGER      PRIMARY KEY AUTOINCREMENT,
    nazwa                VARCHAR(256) NOT NULL,
    adres                VARCHAR(256) NOT NULL,
    nip                  VARCHAR(10)  UNIQUE,
    zopz_id              INTEGER      NOT NULL REFERENCES uzytkownik(id),
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE praktyka (
    id                INTEGER     PRIMARY KEY AUTOINCREMENT,
    student_id        INTEGER     NOT NULL REFERENCES uzytkownik(id),
    uopz_id           INTEGER     NOT NULL REFERENCES uzytkownik(id),
    zaklad_id         INTEGER     NOT NULL REFERENCES zaklad(id),
    data_rozpoczecia  DATE        NOT NULL,
    data_zakonczenia  DATE        NOT NULL,
    status            VARCHAR(16) NOT NULL DEFAULT 'draft'
                                  CHECK (status IN (
                                      'draft','submitted','active',
                                      'completed','under_review',
                                      'approved','rejected','closed'
                                  )),
    created_at        DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE efekt_uczenia (
    id    INTEGER     PRIMARY KEY AUTOINCREMENT,
    kod   VARCHAR(4)  NOT NULL UNIQUE,
    opis  TEXT        NOT NULL
);

CREATE TABLE wpis_dziennika (
    id              INTEGER  PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER  NOT NULL REFERENCES praktyka(id),
    data_wpisu      DATE     NOT NULL,
    opis_prac       TEXT     NOT NULL,
    potwierdzony    BOOLEAN  NOT NULL DEFAULT 0,
    potwierdzone_at DATETIME,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wpis_efekt (
    wpis_id   INTEGER NOT NULL REFERENCES wpis_dziennika(id),
    efekt_id  INTEGER NOT NULL REFERENCES efekt_uczenia(id),
    PRIMARY KEY (wpis_id, efekt_id)
);

CREATE TABLE dokument (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER     NOT NULL REFERENCES praktyka(id),
    typ             VARCHAR(16) NOT NULL CHECK (typ IN (
                        'zal_2a','zal_3','zal_4',
                        'zal_5','zal_6','zal_7','zal_8'
                    )),
    zawartosc_json  TEXT        NOT NULL,
    status          VARCHAR(16) NOT NULL DEFAULT 'draft'
                                CHECK (status IN (
                                    'draft','submitted',
                                    'approved','rejected'
                                )),
    uwagi           TEXT,
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ocena_koncowa (
    id              INTEGER  PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER  NOT NULL UNIQUE REFERENCES praktyka(id),
    ocena_e         REAL     CHECK (ocena_e BETWEEN 2.0 AND 5.0),
    ocena_s         REAL     CHECK (ocena_s BETWEEN 2.0 AND 5.0),
    ocena_u         REAL     CHECK (ocena_u BETWEEN 2.0 AND 5.0),
    ocena_z         REAL     CHECK (ocena_z BETWEEN 2.0 AND 5.0),
    ocena_k         REAL     GENERATED ALWAYS AS
                        (ROUND(0.4*ocena_e + 0.1*ocena_s
                             + 0.2*ocena_u + 0.3*ocena_z, 2)) STORED,
    data_egzaminu   DATE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hospitacja (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    praktyka_id INTEGER  NOT NULL REFERENCES praktyka(id),
    uopz_id     INTEGER  NOT NULL REFERENCES uzytkownik(id),
    data_wizyty DATE     NOT NULL,
    notatki     TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wniosek_zaliczenie (
    id             INTEGER     PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER     NOT NULL REFERENCES uzytkownik(id),
    dyrektor_id    INTEGER     REFERENCES uzytkownik(id),
    uzasadnienie   TEXT        NOT NULL,
    typ_podstawy   VARCHAR(16) NOT NULL CHECK (typ_podstawy IN (
                       'praca','staz','dzialalnosc'
                   )),
    status         VARCHAR(16) NOT NULL DEFAULT 'pending'
                               CHECK (status IN (
                                   'pending','approved',
                                   'partial','rejected'
                               )),
    decyzja_opis   TEXT,
    created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    uzytkownik_id   INTEGER     REFERENCES uzytkownik(id),
    akcja           VARCHAR(16) NOT NULL CHECK (akcja IN (
                        'insert','update','delete','login','logout'
                    )),
    tabela          VARCHAR(64) NOT NULL,
    rekord_id       INTEGER,
    stara_wartosc   TEXT,
    nowa_wartosc    TEXT,
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Dane słownikowe – 13 efektów uczenia z regulaminu
INSERT INTO efekt_uczenia (kod, opis) VALUES
('E01', 'Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych'),
('E02', 'Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce'),
('E03', 'Zna ekonomiczne, prawne skutki własnych działań oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy'),
('E04', 'Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka'),
('E05', 'Pozyskuje informacje z różnych źródeł w języku polskim i angielskim'),
('E06', 'Potrafi podnieść kompetencje z co najmniej dwóch zakresów: sprzęt i oprogramowanie'),
('E07', 'Opracowuje dokumentację i referuje ustnie zagadnienia z praktyki'),
('E08', 'Potrafi zidentyfikować problem informatyczny, opisać go i zrealizować koncepcję rozwiązania'),
('E09', 'Rozwiązuje rzeczywiste zadanie inżynierskie stosując normy i aspekty etyczne'),
('E10', 'Pracuje w zespole branży IT'),
('E11', 'Przestrzega zasad etyki zawodowej'),
('E12', 'Potrafi komunikować się z osobami spoza branży'),
('E13', 'Dostrzega tempo deaktualizacji wiedzy i skutki działalności informatyków');