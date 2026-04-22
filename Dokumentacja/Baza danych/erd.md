erDiagram

&#x20;   UZYTKOWNIK {

&#x20;       int id PK

&#x20;       string imie

&#x20;       string nazwisko

&#x20;       string email

&#x20;       string haslo\_hash

&#x20;       string rola

&#x20;       datetime created\_at

&#x20;   }



&#x20;   ZAKLAD {

&#x20;       int id PK

&#x20;       string nazwa

&#x20;       string adres

&#x20;       string nip

&#x20;       string opiekun\_imie

&#x20;       string opiekun\_nazwisko

&#x20;       string opiekun\_stanowisko

&#x20;       string opiekun\_email

&#x20;       string opiekun\_telefon

&#x20;       datetime created\_at

&#x20;   }



&#x20;   PRAKTYKA {

&#x20;       int id PK

&#x20;       int student\_id FK

&#x20;       int uopz\_id FK

&#x20;       int zopz\_id FK

&#x20;       int zaklad\_id FK

&#x20;       date data\_rozpoczecia

&#x20;       date data\_zakonczenia

&#x20;       int liczba\_dni

&#x20;       string status

&#x20;       datetime created\_at

&#x20;       datetime updated\_at

&#x20;   }



&#x20;   WPIS\_DZIENNIKA {

&#x20;       int id PK

&#x20;       int praktyka\_id FK

&#x20;       date data\_wpisu

&#x20;       text opis\_prac

&#x20;       bool potwierdzony

&#x20;       datetime potwierdzone\_at

&#x20;       datetime created\_at

&#x20;   }



&#x20;   WPIS\_EFEKT {

&#x20;       int wpis\_id FK

&#x20;       int efekt\_id FK

&#x20;   }



&#x20;   EFEKT\_UCZENIA {

&#x20;       int id PK

&#x20;       string kod

&#x20;       text opis

&#x20;   }



&#x20;   DOKUMENT {

&#x20;       int id PK

&#x20;       int praktyka\_id FK

&#x20;       string typ

&#x20;       text zawartosc\_json

&#x20;       string status

&#x20;       text uwagi

&#x20;       datetime created\_at

&#x20;       datetime updated\_at

&#x20;   }



&#x20;   OCENA\_KONCOWA {

&#x20;       int id PK

&#x20;       int praktyka\_id FK

&#x20;       float ocena\_e

&#x20;       float ocena\_s

&#x20;       float ocena\_u

&#x20;       float ocena\_z

&#x20;       float ocena\_k

&#x20;       datetime data\_egzaminu

&#x20;       datetime created\_at

&#x20;   }



&#x20;   HOSPITACJA {

&#x20;       int id PK

&#x20;       int praktyka\_id FK

&#x20;       int uopz\_id FK

&#x20;       date data\_wizyty

&#x20;       text notatki

&#x20;       datetime created\_at

&#x20;   }



&#x20;   WNIOSEK\_ZALICZENIE {

&#x20;       int id PK

&#x20;       int student\_id FK

&#x20;       int dyrektor\_id FK

&#x20;       text uzasadnienie

&#x20;       string typ\_podstawy

&#x20;       string status

&#x20;       text decyzja\_opis

&#x20;       datetime created\_at

&#x20;       datetime updated\_at

&#x20;   }



&#x20;   AUDIT\_LOG {

&#x20;       int id PK

&#x20;       int uzytkownik\_id FK

&#x20;       string akcja

&#x20;       string tabela

&#x20;       int rekord\_id

&#x20;       text stara\_wartosc

&#x20;       text nowa\_wartosc

&#x20;       datetime created\_at

&#x20;   }



&#x20;   UZYTKOWNIK ||--o{ PRAKTYKA : "jest studentem"

&#x20;   UZYTKOWNIK ||--o{ PRAKTYKA : "jest UOPZ"

&#x20;   ZAKLAD ||--o{ PRAKTYKA : "przyjmuje"

&#x20;   PRAKTYKA ||--o{ WPIS\_DZIENNIKA : "zawiera"

&#x20;   WPIS\_DZIENNIKA ||--o{ WPIS\_EFEKT : "dotyczy"

&#x20;   EFEKT\_UCZENIA ||--o{ WPIS\_EFEKT : "realizowany przez"

&#x20;   PRAKTYKA ||--o{ DOKUMENT : "posiada"

&#x20;   PRAKTYKA ||--|| OCENA\_KONCOWA : "kończy się"

&#x20;   PRAKTYKA ||--o{ HOSPITACJA : "obejmuje"

&#x20;   UZYTKOWNIK ||--o{ HOSPITACJA : "przeprowadza"

&#x20;   UZYTKOWNIK ||--o{ WNIOSEK\_ZALICZENIE : "składa"

&#x20;   UZYTKOWNIK ||--o{ AUDIT\_LOG : "generuje"

