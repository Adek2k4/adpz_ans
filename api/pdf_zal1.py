"""PDF generator for Załącznik nr 1 – Porozumienie."""
import os
from io import BytesIO

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


# ── Font registration ──────────────────────────────────────────────────────────
# Try known TTF locations: Windows first, then common Linux paths (Docker).
_FONT_CANDIDATES = [
    {
        "regular":    "C:/Windows/Fonts/times.ttf",
        "bold":       "C:/Windows/Fonts/timesbd.ttf",
        "italic":     "C:/Windows/Fonts/timesi.ttf",
        "bolditalic": "C:/Windows/Fonts/timesbi.ttf",
    },
    {
        "regular":    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "bold":       "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "italic":     "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "bolditalic": "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
    },
    {
        "regular":    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "bold":       "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "italic":     "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "bolditalic": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
    },
]

_BASE  = "DocSerif"
_BOLD  = "DocSerif-Bold"
_ITAL  = "DocSerif-Italic"
_BI    = "DocSerif-BoldItalic"


def _register_fonts():
    for cand in _FONT_CANDIDATES:
        if not os.path.exists(cand["regular"]):
            continue
        pdfmetrics.registerFont(TTFont(_BASE, cand["regular"]))
        pdfmetrics.registerFont(TTFont(_BOLD, cand["bold"]))
        pdfmetrics.registerFont(TTFont(_ITAL, cand["italic"]))
        pdfmetrics.registerFont(TTFont(_BI,   cand["bolditalic"]))
        pdfmetrics.registerFontFamily(
            _BASE, normal=_BASE, bold=_BOLD, italic=_ITAL, boldItalic=_BI
        )
        return True
    return False


_fonts_ok = _register_fonts()

# Fall back to built-in Type1 fonts if no TTF found (Polish chars will be squares)
_F  = _BASE if _fonts_ok else "Times-Roman"
_FB = _BOLD if _fonts_ok else "Times-Bold"
_FI = _ITAL if _fonts_ok else "Times-Italic"
_FBI = _BI  if _fonts_ok else "Times-BoldItalic"


# ── Paragraph styles ───────────────────────────────────────────────────────────
def _style(name, **kw):
    base = dict(fontName=_F, fontSize=11, leading=16, spaceAfter=0, spaceBefore=0)
    base.update(kw)
    return ParagraphStyle(name, **base)


S_NORMAL   = _style("normal",   alignment=TA_JUSTIFY)
S_RIGHT    = _style("right",    alignment=TA_RIGHT, fontSize=10)
S_CENTER   = _style("center",   alignment=TA_CENTER)
S_CENTER_B = _style("centerB",  alignment=TA_CENTER, fontName=_FBI, fontSize=12)
S_LABEL    = _style("label",    fontSize=9, alignment=TA_CENTER, textColor="grey")
S_SIG      = _style("sig",      fontSize=10, alignment=TA_CENTER, fontName=_FI)


def _p(text, style=None):
    return Paragraph(text, style or S_NORMAL)


def _sp(h=0.4):
    return Spacer(1, h * cm)


def _sig_val(raw):
    if not raw:
        return "..............................................."
    return raw.replace("\n", "<br/>")


# ── Main generator ─────────────────────────────────────────────────────────────
def generate_zal1_pdf(praktyka: dict, dok: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=3 * cm,
        rightMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
    )

    numer        = dok.get("numer") or "..."
    data         = dok.get("data") or "............."
    repr_uczelni = dok.get("repr_uczelni") or "................................."
    repr_zakladu = dok.get("repr_zakladu") or "................................."
    zaklad_nazwa = praktyka.get("zaklad_nazwa") or "................................."
    student_name = praktyka.get("student_name") or "................................."
    data_od      = praktyka.get("data_rozpoczecia") or "..........."
    data_do      = praktyka.get("data_zakonczenia") or "..........."
    pod_uczelnia = dok.get("podpis_uczelnia") or ""
    pod_zaklad   = dok.get("podpis_zaklad") or ""

    story = []

    # Nagłówek
    story.append(_p("Załącznik nr 1", S_RIGHT))
    story.append(_sp(0.6))

    story.append(_p("<i><b>Porozumienie Nr " + numer + "</b></i>", S_CENTER_B))
    story.append(_p("<i><b>w sprawie praktyk studenckich</b></i>", S_CENTER_B))
    story.append(_sp(0.8))

    # Wstęp
    wstep = (
        "zawarte w dniu <b>" + data + "</b> pomiędzy <b>Akademią Nauk Stosowanych "
        "w Elblągu</b>, ul. Wojska Polskiego 1, 82-300 Elbląg zwaną dalej "
        "„Uczelnią” reprezentowaną przez <b>" + repr_uczelni + "</b> z jednej strony, "
        "a <b>" + zaklad_nazwa + "</b>, zwanym dalej „Zakładem pracy”, reprezentowanym "
        "przez <b>" + repr_zakladu + "</b> –– z drugiej strony."
    )
    story.append(_p(wstep))
    story.append(_sp(0.8))

    # § 1. Tabela studenta
    story.append(_p("1.\tUczelnia kieruje studentów Uczelni na praktyki zawodowe na wskazany okres:"))
    story.append(_sp(0.3))

    tbl_data = [
        [
            _p("<b>Lp.</b>", S_CENTER),
            _p("<b>Imię i nazwisko</b>", S_CENTER),
            _p("<b>Termin odbywania<br/>praktyki zawodowej</b>", S_CENTER),
            _p("<b>Wymiar<br/>praktyki zawodowej</b>", S_CENTER),
        ],
        [
            _p("1.", S_CENTER),
            _p(student_name, S_CENTER),
            _p(data_od + " – " + data_do, S_CENTER),
            _p("120 dni roboczych<br/>(960 godz.)", S_CENTER),
        ],
    ]
    tbl = Table(tbl_data, colWidths=[1.2 * cm, 5.5 * cm, 4.5 * cm, 4.0 * cm])
    tbl.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, "black"),
        ("BACKGROUND",    (0, 0), (-1, 0),  "#f0f0f0"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tbl)
    story.append(_sp(0.8))

    # § 2. Obowiązki Zakładu
    story.append(_p("2.\tObowiązki Zakładu pracy:"))
    story.append(_sp(0.2))
    story.append(_p(
        "Zakład pracy zobowiązuje się do sprawowania nadzoru nad studentami odbywającymi "
        "praktykę oraz zapewnienia warunków niezbędnych do jej przeprowadzenia zgodnie "
        "z porozumieniem zawartym z Uczelnią, a w szczególności do:"
    ))
    story.append(_sp(0.15))
    for i, txt in enumerate([
        "zapewnienia odpowiednich stanowisk pracy, urządzeń, pomieszczeń, zgodnie z programem praktyki,",
        "zapoznania studentów z zakładowym regulaminem pracy, z przepisami o bezpieczeństwie i higienie "
        "pracy oraz o ochronie tajemnicy państwowej i służbowej,",
        "sprawowania nadzoru nad właściwym wykonaniem przez studentów programu praktyki,",
        "umożliwienia studentom korzystania z zaplecza socjalnego jakie posiada zakład pracy.",
    ], 1):
        story.append(_p(str(i) + ")\t" + txt))
    story.append(_sp(0.5))

    # § 3. Obowiązki Uczelni
    story.append(_p("3.\tObowiązki Uczelni:"))
    story.append(_sp(0.2))
    story.append(_p("Uczelnia zobowiązana jest do:"))
    story.append(_sp(0.15))
    for i, txt in enumerate([
        "opracowania w porozumieniu z Zakładem pracy i ze studentami szczegółowych programów praktyk,",
        "sprawowania nadzoru dydaktyczno – wychowawczego oraz organizacyjnego nad przebiegiem praktyk.",
    ], 1):
        story.append(_p(str(i) + ")\t" + txt))
    story.append(_sp(0.5))

    # § 4. Obowiązki studenta
    story.append(_p("4.\tObowiązki studenta:"))
    story.append(_sp(0.15))
    for i, txt in enumerate([
        "stosowanie się do ustaleń Zakładu pracy w zakresie porządku i dyscypliny pracy,",
        "przestrzeganie zasad BHP i ochrony przeciwpożarowej,",
        "przestrzeganie zasad odbywania praktyk określonych przez Uczelnię,",
        "student odbywający praktykę zawodową jest zobowiązany ubezpieczyć się indywidualnie "
        "od następstw nieszczęśliwych wypadków na czas trwania praktyki.",
    ], 1):
        story.append(_p(str(i) + ")\t" + txt))
    story.append(_sp(0.5))

    # § 5–8
    for txt in [
        "5.\tUpoważnionym do rozstrzygania, wspólnie z kierownikiem Zakładu pracy, spraw "
        "związanych z przebiegiem praktyki jest opiekun ds. praktyk powołany przez Rektora "
        "Akademii Nauk Stosowanych w Elblągu.",
        "6.\tPorozumienie zostaje zawarte na czas trwania praktyki.",
        "7.\tWszelkie zmiany porozumienia wymagają formy pisemnej pod rygorem nieważności.",
        "8.\tPorozumienie niniejsze sporządzone zostało w dwóch jednobrzmiących egzemplarzach "
        "po jednym dla każdej ze stron.",
    ]:
        story.append(_p(txt))
        story.append(_sp(0.35))

    story.append(_sp(1.2))

    # Podpisy
    sig_tbl = Table(
        [
            [_p(_sig_val(pod_uczelnia), S_SIG),  _p(_sig_val(pod_zaklad), S_SIG)],
            [_p("(podpis Dyrektora Instytutu)", S_LABEL),
             _p("(podpis osoby uprawnionej do reprezentacji<br/>w imieniu Zakładu pracy)", S_LABEL)],
        ],
        colWidths=[7.5 * cm, 7.5 * cm],
    )
    sig_tbl.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0),  0.5, "black"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_tbl)

    doc.build(story)
    return buf.getvalue()
