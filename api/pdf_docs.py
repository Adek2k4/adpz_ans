"""PDF generators for all praktyka documents + dziennik.

Each generator takes (praktyka: dict, dok: dict) and returns PDF bytes.
The dziennik generator takes (praktyka, wpisy, pages).
GENERATORS maps a document type to its generator function.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import PageBreak, SimpleDocTemplate, Table, TableStyle

from .db import EFEKTY_UCZENIA
from .pdf_common import (
    FB,
    P, SP, val, sig_val, new_doc,
    zal_label, ans_header, title, sig_block, kv,
    S_NORMAL, S_LEFT, S_RIGHT, S_CENTER, S_CENTER_B, S_H3,
    S_SMALL, S_SMALL_C, S_CELL, S_LI, S_SUB, S_SIG, S_LABEL,
)

GRID = [
    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
]
HEADER_BG = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaeaea")),
             ("FONTNAME", (0, 0), (-1, 0), FB)]


def _meta(praktyka):
    return (
        praktyka.get("student_name") or "",
        praktyka.get("zaklad_nazwa") or "",
        praktyka.get("data_rozpoczecia") or "",
        praktyka.get("data_zakonczenia") or "",
        praktyka.get("zopz_name") or "",
        praktyka.get("uopz_name") or "",
    )


def _rok_akademicki(data_rozpoczecia):
    """Derive academic year (e.g. '2024/2025') from the practice start date."""
    if not data_rozpoczecia or len(data_rozpoczecia) < 7:
        return ""
    try:
        year = int(data_rozpoczecia[:4])
        month = int(data_rozpoczecia[5:7])
    except (ValueError, TypeError):
        return ""
    if month >= 10:
        return f"{year}/{year + 1}"
    return f"{year - 1}/{year}"


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 1 – Porozumienie
# ═══════════════════════════════════════════════════════════════════════════════
def gen_zal1(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf, left=3 * cm, right=2.5 * cm)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []

    zal_label(story, "Załącznik nr 1")
    story.append(P("<i><b>Porozumienie Nr " + val(dok.get("numer"), "………") + "</b></i>", S_CENTER_B))
    story.append(P("<i><b>w sprawie praktyk studenckich</b></i>", S_CENTER_B))
    story.append(SP(0.7))

    story.append(P(
        "zawarte w dniu <b>" + val(dok.get("data"), "…………") + "</b> pomiędzy "
        "<b>Akademią Nauk Stosowanych w Elblągu</b>, ul. Wojska Polskiego 1, 82-300 Elbląg "
        "zwaną dalej „Uczelnią” reprezentowaną przez <b>" + val(dok.get("repr_uczelni"), "……………") +
        "</b> z jednej strony, a <b>" + val(zaklad, "……………") + "</b>, zwanym dalej "
        "„Zakładem pracy”, reprezentowanym przez <b>" + val(dok.get("repr_zakladu"), "……………") +
        "</b> –– z drugiej strony."
    ))
    story.append(SP(0.7))

    story.append(P("1.\tUczelnia kieruje studentów Uczelni na praktyki zawodowe na wskazany okres:"))
    story.append(SP(0.3))
    t = Table([
        [P("<b>Lp.</b>", S_CENTER), P("<b>Imię i nazwisko</b>", S_CENTER),
         P("<b>Termin odbywania<br/>praktyki zawodowej</b>", S_CENTER),
         P("<b>Wymiar<br/>praktyki zawodowej</b>", S_CENTER)],
        [P("1.", S_CENTER), P(val(student, "—"), S_CENTER),
         P(val(dod, "—") + " – " + val(ddo, "—"), S_CENTER),
         P("120 dni roboczych<br/>(960 godz.)", S_CENTER)],
    ], colWidths=[1.2 * cm, 5.3 * cm, 4.5 * cm, 4.0 * cm])
    t.setStyle(TableStyle(GRID + HEADER_BG))
    story.append(t)
    story.append(SP(0.6))

    story.append(P("2.\tObowiązki Zakładu pracy:"))
    story.append(P(
        "Zakład pracy zobowiązuje się do sprawowania nadzoru nad studentami odbywającymi praktykę "
        "oraz zapewnienia warunków niezbędnych do jej przeprowadzenia, a w szczególności do:"))
    for i, t_ in enumerate([
        "zapewnienia odpowiednich stanowisk pracy, urządzeń, pomieszczeń, zgodnie z programem praktyki,",
        "zapoznania studentów z zakładowym regulaminem pracy, z przepisami BHP oraz o ochronie tajemnicy państwowej i służbowej,",
        "sprawowania nadzoru nad właściwym wykonaniem przez studentów programu praktyki,",
        "umożliwienia studentom korzystania z zaplecza socjalnego jakie posiada zakład pracy.",
    ], 1):
        story.append(P(str(i) + ")\t" + t_))
    story.append(SP(0.4))

    story.append(P("3.\tObowiązki Uczelni:"))
    for i, t_ in enumerate([
        "opracowania w porozumieniu z Zakładem pracy i ze studentami szczegółowych programów praktyk,",
        "sprawowania nadzoru dydaktyczno – wychowawczego oraz organizacyjnego nad przebiegiem praktyk.",
    ], 1):
        story.append(P(str(i) + ")\t" + t_))
    story.append(SP(0.4))

    story.append(P("4.\tObowiązki studenta:"))
    for i, t_ in enumerate([
        "stosowanie się do ustaleń Zakładu pracy w zakresie porządku i dyscypliny pracy,",
        "przestrzeganie zasad BHP i ochrony przeciwpożarowej,",
        "przestrzeganie zasad odbywania praktyk określonych przez Uczelnię,",
        "ubezpieczenie się indywidualnie od następstw nieszczęśliwych wypadków na czas trwania praktyki.",
    ], 1):
        story.append(P(str(i) + ")\t" + t_))
    story.append(SP(0.4))

    for t_ in [
        "5.\tUpoważnionym do rozstrzygania spraw związanych z przebiegiem praktyki jest opiekun "
        "ds. praktyk powołany przez Rektora ANS w Elblągu.",
        "6.\tPorozumienie zostaje zawarte na czas trwania praktyki.",
        "7.\tWszelkie zmiany porozumienia wymagają formy pisemnej pod rygorem nieważności.",
        "8.\tPorozumienie sporządzono w dwóch jednobrzmiących egzemplarzach po jednym dla każdej ze stron.",
    ]:
        story.append(P(t_))
        story.append(SP(0.3))

    story.append(SP(1.2))
    sig_block(story, [
        (dok.get("podpis_uczelnia"), "(podpis Dyrektora Instytutu)"),
        (dok.get("podpis_zaklad"), "(podpis osoby uprawnionej do reprezentacji<br/>w imieniu Zakładu pracy)"),
    ])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 2 – Program praktyki
# ═══════════════════════════════════════════════════════════════════════════════
def gen_zal2(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    story = []
    zal_label(story, "Załącznik nr 2.")
    title(story, "PROGRAM PRAKTYKI")

    # ── A. Etap pierwszy ──────────────────────────────────────
    story.append(P("<b>A. Etap pierwszy – rozpoczęcie praktyki</b>", S_H3))
    story.append(SP(0.15))
    for i, t_ in enumerate([
        "Czynności organizacyjne, szkolenie BHP i ppoż.",
        "Zapoznanie się z zakresem działania zakładu pracy (rodzaj usług, produkcja, struktura "
        "organizacyjna itp.) ze szczególnym uwzględnieniem stanowisk informatycznych.",
        "Zapoznanie z projektami realizowanymi przez firmę, środkami produkcji, aplikacjami "
        "użytkowymi, stosowanymi technologiami informatycznymi z podkreśleniem wytwórczych "
        "narzędzi softwareowych i sieci komputerowych.",
    ], 1):
        story.append(P(str(i) + ")&nbsp;&nbsp;" + t_, S_LI))
    story.append(SP(0.35))

    # ── B. Etap drugi ─────────────────────────────────────────
    story.append(P("<b>B. Etap drugi</b>", S_H3))
    story.append(SP(0.15))
    story.append(P(
        "1)&nbsp;&nbsp;Praca na ostatecznym stanowisku pracy, wykonywanie prac i projektów "
        "informatycznych tak aby osiągnąć poniższe, wymagane programem studiów, efekty uczenia się:",
        S_LI))
    sub = [
        "ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki "
        "z zachowaniem standardów i norm technicznych;",
        "zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce;",
        "zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki "
        "oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy;",
        "zna podstawowe zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka;",
        "pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do "
        "realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi "
        "i zasobami publikowanymi w języku polskim jak i angielskim;",
        "rozwiązuje praktyczne problemy informatyczne osadzone w środowisku zajmującym się "
        "zawodowo działalnością inżynierską w branży IT, stosując normy i standardy stosowane "
        "w informatyce, a także zasady ergonomii i bezpieczeństwa oraz biorąc pod uwagę aspekty "
        "środowiskowe i etyczne;",
        "opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, "
        "a także referuje ustnie prezentowane w niej zagadnienia;",
        "pracuje w zespole zajmującym się zawodowo branżą IT;",
        "przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy "
        "i pomocy doświadczonych kolegów;",
        "kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne "
        "informacje do realizacji planowanego zadania, jak i przekazać im w sposób zrozumiały "
        "informacje i opinie z zakresu informatyki;",
        "dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki "
        "działalności informatyków szczególnie te ekonomiczne i społeczne.",
    ]
    for letter, t_ in zip("abcdefghijk", sub):
        story.append(P(letter + ")&nbsp;&nbsp;" + t_, S_SUB))
    story.append(P(
        "2)&nbsp;&nbsp;Opcjonalnie formułowanie przez zakład pracy tematu pracy dyplomowej "
        "i precyzowanie zakresu pracy dyplomowej; rozpoczęcie realizacji pracy dyplomowej pod "
        "nadzorem opiekuna pracy ze strony uczelni oraz konsultanta ze strony zakładu pracy.",
        S_LI))
    story.append(P(
        "3)&nbsp;&nbsp;Planowany czas realizacji praktyki: 6 miesięcy tj. 120 dni (960 godz.).",
        S_LI))
    story.append(SP(0.35))

    # ── C. Etap trzeci ────────────────────────────────────────
    story.append(P("<b>C. Etap trzeci – zakończenie praktyki</b>", S_H3))
    story.append(SP(0.15))
    for i, t_ in enumerate([
        "W trakcie praktyki student prowadzi „Dzienniczek praktyki”. Wpisy w dzienniczku powinny "
        "być potwierdzone przez zakładowego opiekuna praktyki.",
        "Na „Karcie praktyki zawodowej” kierownik zakładu pracy potwierdza odbycie praktyki "
        "a opiekun zakładowy wystawia ocenę parametryczną i w formie opisowej.",
        "Opiekun ze strony zakładu pracy na odpowiednim druku „Potwierdzenie efektów uczenia się” "
        "potwierdza osiągnięcie przez praktykanta wymienionych powyżej efektów uczenia się.",
    ], 1):
        story.append(P(str(i) + ")&nbsp;&nbsp;" + t_, S_LI))
    story.append(SP(2.0))

    sig_block(story, [
        (dok.get("podpis_zakladu"), "zakład pracy"),
        (dok.get("podpis_dyrektora"), "dyrektor Instytutu"),
    ])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 2a – Program i harmonogram
# ═══════════════════════════════════════════════════════════════════════════════
def gen_zal2a(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, "Załącznik nr 2a")
    ans_header(story)
    story.append(P("Kierunek studiów: <b><i>Informatyka</i></b>", S_LEFT)); story.append(SP(0.2))
    kv(story, "Student / ka", student)
    kv(story, "Nr albumu", praktyka.get("nr_albumu"))
    kv(story, "Specjalność", praktyka.get("specjalnosc"))
    kv(story, "Miejsce praktyki (instytucja)", zaklad)
    story.append(P("<b>Termin realizacji praktyki:</b> od " + val(dod, "………") +
                   " do " + val(ddo, "………") + "    <b>Liczba dni roboczych:</b> 120"))
    story.append(SP(0.5))
    title(story, "PROGRAM PRAKTYKI ZAWODOWEJ")

    # Efekty → dział/prace
    ef_map = {}
    for ef in (dok.get("efekty") or []):
        ef_map[ef.get("nr")] = ef.get("dzial_czynnosci") or ""
    rows = [[P("<b>Nr</b>", S_SMALL_C), P("<b>Efekty kształcenia</b>", S_SMALL_C),
             P("<b>Dział (komórka) / przykładowe prace<br/>wykonywane przez praktykanta</b>", S_SMALL_C)]]
    for nr, opis in EFEKTY_UCZENIA:
        rows.append([P(nr, S_SMALL_C), P(opis, S_CELL), P(ef_map.get(nr, ""), S_CELL)])
    t = Table(rows, colWidths=[1.0 * cm, 9.0 * cm, 6.5 * cm], repeatRows=1)
    t.setStyle(TableStyle(GRID + HEADER_BG + [("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t)
    story.append(SP(0.5))

    title(story, "HARMONOGRAM PRAKTYKI ZAWODOWEJ")
    hrows = [[P("<b>L.p.</b>", S_SMALL_C),
              P("<b>Dział / komórka (miejsce odbywania praktyki)</b>", S_SMALL_C),
              P("<b>Planowana liczba<br/>dni roboczych</b>", S_SMALL_C)]]
    total = 0
    harm = dok.get("harmonogram") or []
    for i, h in enumerate(harm, 1):
        dni = h.get("dni") or ""
        try:
            total += int(dni)
        except (ValueError, TypeError):
            pass
        hrows.append([P(str(i), S_SMALL_C), P(h.get("dzial") or "", S_CELL), P(str(dni), S_SMALL_C)])
    hrows.append([P("", S_SMALL_C), P("<b>Łącznie</b>", S_SMALL), P("<b>" + str(total) + "</b>", S_SMALL_C)])
    hrows.append([P("", S_SMALL_C), P("<b>Wymagana</b>", S_SMALL), P("<b>120</b>", S_SMALL_C)])
    ht = Table(hrows, colWidths=[1.2 * cm, 11.3 * cm, 4.0 * cm])
    ht.setStyle(TableStyle(GRID + HEADER_BG))
    story.append(ht)
    story.append(SP(0.5))

    story.append(P("Uzgodniono w dniu: " + val(dok.get("data_uzgodnienia"), "…………………………")))
    story.append(SP(1.2))
    sig_block(story, [
        (dok.get("podpis_uopz"), "podpis uczelnianego<br/>opiekuna praktyki"),
        (dok.get("podpis_zopz"), "podpis zakładowego<br/>opiekuna praktyki"),
        (dok.get("podpis_student"), "podpis studenta"),
    ])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 3.1 – Skierowanie na praktykę
# ═══════════════════════════════════════════════════════════════════════════════
def gen_zal3_1(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, "Załącznik nr 3")
    ans_header(story)
    title(story, "KARTA PRAKTYKI ZAWODOWEJ")
    story.append(P("<b>SKIEROWANIE NA PRAKTYKĘ</b>", S_CENTER))
    story.append(SP(0.4))
    story.append(P(
        "Na podstawie porozumienia nr <b>" + val(dok.get("nr_porozumienia"), "……") + "</b>, "
        "z dnia <b>" + val(dok.get("data_porozumienia"), "…………") + "</b> r., kieruję niżej "
        "wymienionego studenta na praktykę zawodową do zakładu pracy:"))
    story.append(P("<b>" + val(zaklad, "……………………") + "</b>", S_CENTER))
    story.append(SP(0.4))
    kv(story, "1. Imię i nazwisko", student)
    kv(story, "2. Numer albumu", praktyka.get("nr_albumu"))
    story.append(P("3. Studia: inżynierskie <b>" + val(dok.get("tryb_studiow"), "stacjonarne / niestacjonarne") + "</b>"))
    story.append(SP(0.25))
    story.append(P("4. Kierunek: <b>informatyka</b>     specjalność: <b>" +
                   val(praktyka.get("specjalnosc"), "…………………") + "</b>"))
    story.append(SP(0.25))
    story.append(P("5. Czas trwania praktyki: <b>6 miesięcy</b> (120 dni roboczych)"))
    story.append(SP(0.25))
    kv(story, "6. Uczelniany opiekun praktyki zawodowej", uopz)
    story.append(P("7. Termin praktyki: od <b>" + val(dod, "…………") + "</b> do <b>" + val(ddo, "…………") + "</b>"))
    story.append(SP(0.3))
    kv(story, "Data skierowania", dok.get("data_skierowania"))
    story.append(SP(1.4))
    sig_block(story, [
        (dok.get("podpis_dyrektor"), "Dyrektor Instytutu lub osoba upoważniona<br/>(podpis)"),
    ], col_w=[10 * cm])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 3.2 – Zgłoszenie / szkolenie BHP
# ═══════════════════════════════════════════════════════════════════════════════
def gen_zal3_2(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, "Załącznik nr 3")
    ans_header(story)
    title(story, "KARTA PRAKTYKI ZAWODOWEJ")
    story.append(P("Zakładowy opiekun praktyki zawodowej:", S_LEFT)); story.append(SP(0.2))
    kv(story, "Imię i nazwisko", zopz)
    kv(story, "Stanowisko", dok.get("stanowisko_zopz"))
    kv(story, "Funkcja / rola", dok.get("funkcja_zopz"))
    story.append(SP(0.5))
    story.append(P("<b>Potwierdzam zgłoszenie się studenta " + val(student, "………") + " na praktykę:</b>"))
    story.append(SP(1.0))
    sig_block(story, [(dok.get("podpis_zopz_1"),
                       "(data, pieczęć i podpis zakładowego opiekuna praktyki)")], col_w=[11 * cm])
    story.append(SP(0.8))
    story.append(P("<b>Potwierdzam odbycie szkolenia BHP:</b>"))
    story.append(SP(1.0))
    sig_block(story, [(dok.get("podpis_zopz_2"),
                       "(data, pieczęć i podpis upoważnionego pracownika zakładu)")], col_w=[11 * cm])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 3.3 – Zaświadczenie odbycia praktyki
# ═══════════════════════════════════════════════════════════════════════════════
def gen_zal3_3(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, "Załącznik nr 3")
    title(story, "Zaświadczenie odbycia praktyki zawodowej")
    story.append(P(
        "Zaświadczam, że student <b>" + val(student, "……………") + "</b> odbył praktykę zawodową "
        "w <b>" + val(zaklad, "……………") + "</b> w okresie od <b>" + val(dod, "………") + "</b> do "
        "<b>" + val(ddo, "………") + "</b> zgodnie z przyjętym programem."))
    story.append(SP(0.4))
    story.append(P("<b>Uwagi:</b> " + val(dok.get("uwagi"), "—")))
    story.append(SP(1.6))
    sig_block(story, [(dok.get("podpis_zopz"), "(pieczęć i podpis kierownika zakładu)")], col_w=[11 * cm])
    doc.build(story)
    return buf.getvalue()


def _ocena_doc(praktyka, dok, zal_no, naglowek, rola_caption, sig_field, by_text):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, zal_no)
    title(story, naglowek)
    story.append(P(
        "Ocena przebiegu praktyki zawodowej studenta <b>" + val(student, "……………") + "</b> "
        + by_text + "."))
    story.append(SP(0.5))
    story.append(P("<b>Ocena parametryczna (w skali 2 do 5):</b> " + val(dok.get("ocena_param"), "………")))
    story.append(SP(0.4))
    story.append(P("<b>Ocena opisowa:</b>"))
    story.append(P(val(dok.get("ocena_opisowa"), "—"), S_NORMAL))
    story.append(SP(1.6))
    sig_block(story, [(dok.get(sig_field), rola_caption)], col_w=[11 * cm])
    doc.build(story)
    return buf.getvalue()


# Załącznik nr 3.4 – Ocena (ZOPZ)
def gen_zal3_4(praktyka, dok):
    return _ocena_doc(praktyka, dok, "Załącznik nr 3",
                      "Ocena przebiegu praktyki zawodowej (Zakład pracy)",
                      "Zakładowy opiekun praktyki zawodowej<br/>(data, pieczęć i podpis)",
                      "podpis_zopz", "wystawiona przez Zakładowego Opiekuna Praktyki Zawodowej")


# Załącznik nr 3.5 – Ocena (UOPZ)
def gen_zal3_5(praktyka, dok):
    return _ocena_doc(praktyka, dok, "Załącznik nr 3",
                      "Ocena przebiegu praktyki zawodowej (Uczelnia)",
                      "Uczelniany opiekun praktyki zawodowej<br/>(data, pieczęć i podpis)",
                      "podpis_uopz", "wystawiona przez Uczelnianego Opiekuna Praktyki Zawodowej")


# Załącznik nr 3.6 – Ocena sprawozdania
def gen_zal3_6(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, "Załącznik nr 3")
    title(story, "Ocena sprawozdania z praktyki")
    story.append(P("Ocena sprawozdania z praktyki zawodowej studenta <b>" + val(student, "……") + "</b>."))
    story.append(SP(0.5))
    story.append(P("<b>Ocena sprawozdania z praktyki (w skali 2 do 5):</b> " + val(dok.get("ocena"), "………")))
    story.append(SP(1.6))
    sig_block(story, [(dok.get("podpis_uopz"), "(data i podpis uczelnianego opiekuna praktyki)")], col_w=[11 * cm])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 4 – Potwierdzenie efektów uczenia się
# ═══════════════════════════════════════════════════════════════════════════════
def gen_zal4(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, "Załącznik nr 4")
    title(story, "POTWIERDZENIE UZYSKANIA EFEKTÓW UCZENIA SIĘ<br/>W RAMACH PRAKTYKI ZAWODOWEJ")
    kv(story, "Student / ka", student)
    kv(story, "Nr albumu", praktyka.get("nr_albumu"))
    story.append(P("Kierunek studiów: <b><i>Informatyka</i></b>"))
    story.append(SP(0.25))
    kv(story, "Specjalność", praktyka.get("specjalnosc"))
    story.append(P("W ramach praktyki zawodowej zrealizowanej w wymiarze <b>" +
                   val(dok.get("liczba_godzin"), "………") + "</b> godzin uzyskał/a "
                   "zakładane dla praktyki zawodowej efekty uczenia się:"))
    story.append(SP(0.4))

    ef = dok.get("efekty") or {}
    rows = [[P("<b>Nr</b>", S_SMALL_C), P("<b>Efekty uczenia się</b>", S_SMALL_C),
             P("<b>Potwierdzenie<br/>uzyskania efektów</b>", S_SMALL_C)]]
    for nr, opis in EFEKTY_UCZENIA:
        got = ef.get(nr)
        mark = "uzyskał/a" if got else "nie uzyskał/a"
        rows.append([P(nr, S_SMALL_C), P(opis, S_CELL), P(mark, S_SMALL_C)])
    t = Table(rows, colWidths=[1.0 * cm, 11.0 * cm, 4.5 * cm], repeatRows=1)
    t.setStyle(TableStyle(GRID + HEADER_BG + [("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t)
    story.append(SP(0.5))

    story.append(P("<b>Potwierdzenie bezpośredniego opiekuna zakładowego:</b>"))
    story.append(SP(0.8))
    sig_block(story, [(dok.get("podpis_zopz"), "Data, podpis i pieczęć zakładu pracy")], col_w=[11 * cm])
    story.append(SP(0.6))
    story.append(P("<b>Opinia opiekuna uczelnianego:</b>"))
    story.append(P(val(dok.get("opinia_uopz"), "—")))
    story.append(SP(1.0))
    sig_block(story, [(dok.get("podpis_uopz"), "Data, podpis opiekuna uczelnianego")], col_w=[11 * cm])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 5 – Kwestionariusz ankiety
# ═══════════════════════════════════════════════════════════════════════════════
_ANKIETA_PYTANIA = [
    "Poznałam/poznałem zasady funkcjonowania instytucji, w której odbywałam/odbywałem praktyki zawodowe.",
    "Poznałam/poznałem strukturę oraz regulamin organizacyjny instytucji, w której odbywałam/odbywałem praktyki zawodowe.",
    "Praktyki zawodowe umożliwiły mi pełną realizację ramowego programu praktyk zawodowych przewidzianego w ramach mojego kierunku studiów.",
    "Podczas praktyk zawodowych zwracano uwagę na przestrzeganie zasad etyki i tajemnicy zawodowej.",
    "Podczas praktyk miałam/miałem możliwość praktycznego zastosowania wiedzy teoretycznej zdobytej na zajęciach.",
    "Praktyki zawodowe przyczyniły się do pogłębienia mojej wiedzy i umiejętności zdobytych w trakcie studiów.",
    "Mogłem liczyć na wsparcie merytoryczne Opiekuna zakładowego praktyk.",
    "Mogłem liczyć na wsparcie merytoryczne Opiekuna uczelnianego praktyk.",
    "Opiekun zakładowy odpowiedzialny za praktyki zawodowe w miejscu ich odbywania potrafił prawidłowo zorganizować ich przebieg.",
    "Podczas praktyk zawodowych miałam/miałem możliwość pozyskiwania materiałów niezbędnych do przygotowania mojej pracy dyplomowej.",
    "Praktyki zawodowe rozwinęły moje umiejętności skutecznego komunikowania się w sytuacjach zawodowych i pracy w zespole.",
    "Praktyki zawodowe nauczyły mnie samodzielności i odpowiedzialności podczas wykonywania pracy.",
    "Liczba godzin realizowana w ramach praktyk zawodowych jest wystarczająca.",
    "Czy po zakończeniu praktyki zawodowej chciałaby/chciałby Pani/Pan współpracować z instytucją, w której Pani/Pan zrealizowała/zrealizował praktykę?",
]
_SKALA = ["zdecydowanie tak", "raczej tak", "trudno powiedzieć", "raczej nie", "zdecydowanie nie"]
_SKALA_HDR = ["zdecydowanie\ntak", "raczej\ntak", "trudno\npowiedzieć", "raczej\nnie", "zdecydowanie\nnie"]


def gen_zal5(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf, top=1.5 * cm, bottom=1.5 * cm)
    story = []
    zal_label(story, "Załącznik nr 5")
    title(story, "Kwestionariusz ankiety oceniający przebieg<br/>praktyk zawodowych")
    story.append(P("Prosimy zaznaczyć przy każdym pytaniu wybraną odpowiedź.", S_SMALL))
    story.append(SP(0.3))

    pytania = dok.get("pytania") or {}
    hdr = [P("", S_SMALL_C)] + [P("<b>" + h.replace("\n", "<br/>") + "</b>", S_SMALL_C) for h in _SKALA_HDR]
    rows = [hdr]
    for idx, pyt in enumerate(_ANKIETA_PYTANIA, 1):
        chosen = pytania.get(str(idx), "")
        cells = [P(str(idx) + ". " + pyt, S_CELL)]
        for s in _SKALA:
            cells.append(P("<b>X</b>" if chosen == s else "", S_SMALL_C))
        rows.append(cells)
    col = [8.0 * cm] + [1.9 * cm] * 5
    t = Table(rows, colWidths=col, repeatRows=1)
    t.setStyle(TableStyle(GRID + HEADER_BG + [("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(t)
    story.append(SP(0.4))

    story.append(P("<b>Dodatkowe uwagi dotyczące przebiegu praktyki zawodowej:</b>"))
    story.append(P(val(dok.get("dodatkowe_uwagi"), "—")))
    story.append(SP(0.4))

    mrows = [
        [P("<b>Rok akademicki</b>", S_CELL), P(val(dok.get("rok_akademicki"), ""), S_CELL)],
        [P("<b>Kierunek studiów</b>", S_CELL), P("Informatyka", S_CELL)],
        [P("<b>Forma studiów</b>", S_CELL), P(val(dok.get("forma_studiow"), ""), S_CELL)],
        [P("<b>Semestr studiów</b>", S_CELL), P(val(dok.get("semestr"), ""), S_CELL)],
        [P("<b>Liczba godzin zrealizowanej praktyki</b>", S_CELL), P(val(dok.get("liczba_godzin"), ""), S_CELL)],
    ]
    mt = Table([[P("<b>Metryczka</b>", S_SMALL_C), ""]] + mrows, colWidths=[7 * cm, 10.5 * cm])
    mt.setStyle(TableStyle(GRID + [("SPAN", (0, 0), (1, 0)),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaeaea")),
                                   ("ALIGN", (0, 0), (-1, 0), "CENTER")]))
    story.append(mt)
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 7 – Sprawozdanie studenta
# ═══════════════════════════════════════════════════════════════════════════════
def gen_zal7(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, "Załącznik nr 7")
    ans_header(story)
    kv(story, "Student", student)
    story.append(P("Kierunek: <b>informatyka</b>, studia inżynierskie stacjonarne"))
    story.append(SP(0.15))
    story.append(P("Specjalność: <b>" + val(praktyka.get("specjalnosc"), "…………………") + "</b>     "
                   "Rok ak.: <b>" + val(_rok_akademicki(dod), "………") + "</b>"))
    story.append(SP(0.3))
    title(story, "SPRAWOZDANIE STUDENTA<br/>Z PRAKTYKI ZAWODOWEJ")
    story.append(P("odbytej w <b>" + val(zaklad, "……………") + "</b>"))
    story.append(SP(0.4))

    story.append(P("<b>I. CHARAKTERYSTYKA MIEJSCA ODBYWANIA PRAKTYKI</b>", S_H3))
    story.append(P(val(dok.get("charakterystyka"), "—")))
    story.append(SP(0.4))
    story.append(P("<b>II. OPIS I ANALIZA WYKONYWANYCH PRAC</b>", S_H3))
    story.append(P(val(dok.get("opis_prac"), "—")))
    story.append(SP(0.4))
    story.append(P("<b>III. WIEDZA I UMIEJĘTNOŚCI UZYSKANE W TRAKCIE PRAKTYKI</b>", S_H3))
    story.append(P(val(dok.get("wiedza_umiejetnosci"), "—")))
    story.append(SP(1.4))
    sig_block(story, [(dok.get("podpis_student"), "data i podpis studenta")], col_w=[10 * cm])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Załącznik nr 8 – Protokół zaliczenia
# ═══════════════════════════════════════════════════════════════════════════════
def _f(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def gen_zal8(praktyka, dok):
    buf = BytesIO()
    doc = new_doc(buf)
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []
    zal_label(story, "Załącznik nr 8")
    ans_header(story)
    kv(story, "Student", student)
    title(story, "PROTOKÓŁ ZALICZENIA PRAKTYKI ZAWODOWEJ (PZ)")

    story.append(P("<b>Miejsce i okres realizacji PZ:</b>"))
    pt = Table([
        [P("<b>Nazwa instytucji (zakładu pracy)</b>", S_SMALL_C), P("<b>Okres / liczba dni</b>", S_SMALL_C)],
        [P(val(zaklad, ""), S_CELL), P(val(dod, "") + " – " + val(ddo, "") + " / 120 dni", S_CELL)],
    ], colWidths=[11.5 * cm, 6.0 * cm])
    pt.setStyle(TableStyle(GRID + HEADER_BG))
    story.append(pt)
    story.append(SP(0.4))

    S, U, Z = dok.get("ocena_S"), dok.get("ocena_U"), dok.get("ocena_Z")
    story.append(P("Ocena za sprawozdanie z praktyki <b>S</b> = " + val(S, "……")))
    story.append(P("Ocena <b>U</b> = " + val(U, "……") + "    Ocena <b>Z</b> = " + val(Z, "……")))
    story.append(P("Data zaliczenia: " + val(dok.get("data_zaliczenia"), "……………")))
    story.append(SP(0.3))

    komisja = dok.get("sklad_komisji") or []
    story.append(P("<b>Skład komisji:</b>"))
    role_lbl = ["Przewodniczący Komisji", "Uczelniany opiekun praktyki zawodowej", "", ""]
    for i in range(4):
        nm = komisja[i] if i < len(komisja) else ""
        story.append(P(str(i + 1) + ". " + val(nm, "………………………") +
                       ("  — " + role_lbl[i] if role_lbl[i] else "")))
    story.append(SP(0.3))

    mz = dok.get("mini_zadania") or []
    mrows = [[P("<b>Lp.</b>", S_SMALL_C), P("<b>Pytania / mini zadania zawodowe</b>", S_SMALL_C),
              P("<b>Oceny cząstkowe (2–5)</b>", S_SMALL_C)]]
    vals = []
    for i in range(3):
        item = mz[i] if i < len(mz) else {}
        o = item.get("ocena", "")
        fo = _f(o)
        if fo:
            vals.append(fo)
        mrows.append([P(str(i + 1), S_SMALL_C), P(item.get("pytanie", "") or "", S_CELL), P(val(o, ""), S_SMALL_C)])
    E = round(sum(vals) / len(vals), 2) if vals else None
    mrows.append([P("", S_SMALL_C),
                  P("<b>Łączna ocena za mini zadania (E)</b>", S_SMALL),
                  P("<b>" + val(E, "……") + "</b>", S_SMALL_C)])
    mt = Table(mrows, colWidths=[1.2 * cm, 12.3 * cm, 4.0 * cm])
    mt.setStyle(TableStyle(GRID + HEADER_BG))
    story.append(mt)
    story.append(SP(0.3))

    sf, uf, zf = _f(S), _f(U), _f(Z)
    K = None
    if E and sf and uf and zf:
        K = round(0.4 * E + 0.1 * sf + 0.2 * uf + 0.3 * zf, 2)
    story.append(P("<b>Ocena końcowa za PZ:</b> 0,4·E + 0,1·S + 0,2·U + 0,3·Z = <b>K = " + val(K, "……") + "</b>"))
    story.append(P("<b>Zaliczam praktykę zawodową na ocenę (K): " + val(K, "………………") + "</b>"))
    story.append(SP(1.2))
    sig_block(story, [(dok.get("podpis_dyrektor"), "Przewodniczący Komisji (podpis)")], col_w=[10 * cm])
    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Dziennik praktyki (Załącznik nr 6)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_dziennik(praktyka, wpisy, pages):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    student, zaklad, dod, ddo, zopz, uopz = _meta(praktyka)
    story = []

    # Title page
    story.append(P("Załącznik nr 6", S_RIGHT))
    story.append(SP(0.3))
    ans_header(story)
    title(story, "DZIENNIK PRAKTYKI ZAWODOWEJ")
    story.append(P("<b>Student:</b> " + val(student, "—") +
                   "     <b>Nr albumu:</b> " + val(praktyka.get("nr_albumu"), "………")))
    story.append(SP(0.25))
    story.append(P("Kierunek: <b>informatyka</b>, studia inżynierskie stacjonarne"))
    story.append(SP(0.25))
    kv(story, "Miejsce odbywania praktyki", zaklad)
    story.append(P("Data rozpoczęcia praktyki: <b>" + val(dod, "…………") + "</b>     "
                   "Data zakończenia praktyki: <b>" + val(ddo, "…………") + "</b>"))
    story.append(SP(0.5))

    hdr = [P("<b>Dzień</b>", S_SMALL_C), P("<b>Data</b>", S_SMALL_C),
           P("<b>Opis wykonanych prac</b>", S_SMALL_C),
           P("<b>Nr efektów<br/>uczenia się</b>", S_SMALL_C)]
    col = [1.8 * cm, 2.8 * cm, 18.6 * cm, 3.5 * cm]

    for pg in pages:
        entries = pg.get("entries") or []
        if not entries:
            continue
        story.append(PageBreak())
        story.append(P("<b>Strona " + str(pg.get("num")) + " — dni " +
                       str(pg.get("from_day")) + "–" + str(pg.get("to_day")) + "</b>", S_LEFT))
        story.append(SP(0.2))
        rows = [hdr]
        for w in entries:
            nef = w.get("nr_efektow") or []
            if isinstance(nef, list):
                nef = ", ".join(str(x) for x in nef)
            rows.append([
                P(str(w.get("numer_dnia", "")), S_SMALL_C),
                P(val(w.get("data_wpisu"), ""), S_SMALL_C),
                P(val(w.get("opis_prac"), ""), S_CELL),
                P(str(nef), S_SMALL_C),
            ])
        t = Table(rows, colWidths=col, repeatRows=1)
        t.setStyle(TableStyle(GRID + HEADER_BG + [("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(t)
        story.append(SP(0.3))

        # ZOPZ signature in the bottom-right corner of a confirmed page
        if pg.get("confirmed"):
            dates = [str(w.get("potwierdzone_at") or "")[:10] for w in entries if w.get("potwierdzone_at")]
            sig_date = max(dates) if dates else ""
            sig_txt = "Podpisano (" + sig_date + ")\n" + zopz if sig_date else "Podpisano\n" + zopz
            inner = Table(
                [[P(sig_val(sig_txt), S_SIG)],
                 [P("Zakładowy opiekun praktyki (ZOPZ)", S_LABEL)]],
                colWidths=[7.5 * cm],
            )
            inner.setStyle(TableStyle([
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            outer = Table([["", inner]], colWidths=[18.7 * cm, 7.5 * cm])
            outer.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.append(outer)

    if not any((pg.get("entries") for pg in pages)):
        story.append(P("Brak wpisów w dzienniku.", S_LEFT))

    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
GENERATORS = {
    "zal1": gen_zal1,
    "zal2": gen_zal2,
    "zal2a": gen_zal2a,
    "zal3_1": gen_zal3_1,
    "zal3_2": gen_zal3_2,
    "zal3_3": gen_zal3_3,
    "zal3_4": gen_zal3_4,
    "zal3_5": gen_zal3_5,
    "zal3_6": gen_zal3_6,
    "zal4": gen_zal4,
    "zal5": gen_zal5,
    "zal7": gen_zal7,
    "zal8": gen_zal8,
}
