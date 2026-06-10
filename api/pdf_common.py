"""Shared PDF helpers: font registration, styles, common building blocks."""
import os

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
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

BASE = "DocSerif"
BOLD = "DocSerif-Bold"
ITAL = "DocSerif-Italic"
BI   = "DocSerif-BoldItalic"


def _register_fonts():
    for cand in _FONT_CANDIDATES:
        if not os.path.exists(cand["regular"]):
            continue
        pdfmetrics.registerFont(TTFont(BASE, cand["regular"]))
        pdfmetrics.registerFont(TTFont(BOLD, cand["bold"]))
        pdfmetrics.registerFont(TTFont(ITAL, cand["italic"]))
        pdfmetrics.registerFont(TTFont(BI,   cand["bolditalic"]))
        pdfmetrics.registerFontFamily(BASE, normal=BASE, bold=BOLD, italic=ITAL, boldItalic=BI)
        return True
    return False


_fonts_ok = _register_fonts()

# Fall back to built-in Type1 fonts if no TTF found (Polish chars become squares).
F   = BASE if _fonts_ok else "Times-Roman"
FB  = BOLD if _fonts_ok else "Times-Bold"
FI  = ITAL if _fonts_ok else "Times-Italic"
FBI = BI   if _fonts_ok else "Times-BoldItalic"


# ── Paragraph styles ───────────────────────────────────────────────────────────
def style(name, **kw):
    base = dict(fontName=F, fontSize=11, leading=15, spaceAfter=0, spaceBefore=0)
    base.update(kw)
    return ParagraphStyle(name, **base)


S_NORMAL   = style("normal",   alignment=TA_JUSTIFY)
S_LEFT     = style("left",     alignment=TA_LEFT)
S_RIGHT    = style("right",    alignment=TA_RIGHT, fontSize=10)
S_CENTER   = style("center",   alignment=TA_CENTER)
S_CENTER_B = style("centerB",  alignment=TA_CENTER, fontName=FB, fontSize=13)
S_TITLE    = style("title",    alignment=TA_CENTER, fontName=FB, fontSize=13, leading=18)
S_H3       = style("h3",       fontName=FB, fontSize=11)
S_LABEL    = style("label",    fontSize=9, alignment=TA_CENTER, textColor="grey")
S_SIG      = style("sig",      fontSize=10, alignment=TA_CENTER, fontName=FI)
S_SMALL    = style("small",    fontSize=9, alignment=TA_JUSTIFY, leading=12)
S_SMALL_C  = style("smallC",   fontSize=9, alignment=TA_CENTER, leading=12)
S_CELL     = style("cell",     fontSize=9, alignment=TA_LEFT, leading=12)
# Numbered list item: hanging indent (1), (2) ...
S_LI       = style("li",       alignment=TA_JUSTIFY, leftIndent=18, firstLineIndent=-18)
# Lettered sub-item a), b) ... – deeper indent
S_SUB      = style("sub",      alignment=TA_JUSTIFY, leftIndent=36, firstLineIndent=-18)


def P(text, st=None):
    return Paragraph(text, st or S_NORMAL)


def SP(h=0.4):
    return Spacer(1, h * cm)


DOTS = "............................................."


def val(v, placeholder=DOTS):
    """Return value or a dotted placeholder when empty."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return placeholder
    return str(v)


def sig_val(raw):
    """Format a stored signature string for display (newline → <br/>)."""
    if not raw:
        return ".........................................."
    return str(raw).replace("\n", "<br/>")


def new_doc(buf, top=2 * cm, bottom=2 * cm, left=2.5 * cm, right=2 * cm):
    return SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=left, rightMargin=right, topMargin=top, bottomMargin=bottom,
    )


def zal_label(story, text):
    """Top-right 'Załącznik nr X' marker."""
    story.append(P(text, S_RIGHT))
    story.append(SP(0.4))


def ans_header(story):
    """Standard institutional header block."""
    story.append(P("<b>Akademia Nauk Stosowanych w Elblągu</b>", S_LEFT))
    story.append(P("<b>Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego</b>", S_LEFT))
    story.append(SP(0.5))


def title(story, text):
    story.append(P(text, S_TITLE))
    story.append(SP(0.6))


def sig_block(story, pairs, col_w=None):
    """
    pairs: list of (signature_value, caption) tuples (1 or 2 columns).
    """
    cells_top = [P(sig_val(v), S_SIG) for v, _ in pairs]
    cells_cap = [P(c, S_LABEL) for _, c in pairs]
    n = len(pairs)
    if col_w is None:
        total = 15.5
        col_w = [total / n * cm] * n
    tbl = Table([cells_top, cells_cap], colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0), 0.5, "black"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)


def kv(story, label, value, placeholder=DOTS):
    """A single 'Label: value' line."""
    story.append(P("<b>" + label + ":</b> " + val(value, placeholder)))
    story.append(SP(0.25))
