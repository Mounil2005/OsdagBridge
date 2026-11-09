"""
Central formatting / style configuration for the OsdagBridge design report.

Single source of truth for page geometry, colours, table style, header/footer
theme, chart style and thresholds. Chapter generators and report_generator.py
must import their formatting values from here instead of hard-coding them.

Everything in this module is plain data or small pure helpers (no I/O), so it
is safe to import from anywhere in the report package.
"""

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
DOCUMENT_CLASS = "report"
FONT_SIZE_PT = 12
PAPER = "a4paper"
PAGE_MARGIN = "1in"            # left / right / top margin
BOTTOM_MARGIN = "1.15in"       # a little extra so rows never touch the footer
FOOTSKIP_PT = 30               # distance from text bottom to footer baseline
LINE_STRETCH = 1.15

A4_WIDTH_CM = 21.0
_MARGIN_CM = 2.54
TEXT_WIDTH_CM = A4_WIDTH_CM - 2 * _MARGIN_CM   # 15.92 cm

# ---------------------------------------------------------------------------
# Colours (HTML hex, no '#')
# ---------------------------------------------------------------------------
COLORS = {
    "osdagGreen": "91B014",
    "headerFill": "EEF3DA",    # light tint of the brand green for table headers
    "failRed":    "C62828",
    "passGreen":  "2E7D32",
    "neutralGrey": "6B6B6B",
}

# ---------------------------------------------------------------------------
# Table style
# ---------------------------------------------------------------------------
TAB_COL_SEP_PT = 6
ARRAY_STRETCH = 1.12
ARRAY_RULE_WIDTH_PT = 0.5
EXTRA_ROW_HEIGHT_PT = 0.6
LT_PRE_PT = 0
LT_POST_PT = 6
LT_CHUNK_SIZE = 60
NEEDSPACE_BASELINES = 5        # start a table on a new page if less room than this
REPEAT_TABLE_HEADERS = True    # repeat the column-header row on continued pages
FIT_TABLES_TO_PAGE = True      # scale p{..cm} column widths down to the text width

# ---------------------------------------------------------------------------
# Header / footer text
# ---------------------------------------------------------------------------
FOOTER_LEFT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
FOOTER_RIGHT = r"Page \thepage\ of \pageref{LastPage}"

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
UR_THRESHOLD = 1.0             # UR = Demand / Capacity; > threshold fails
CHART_DPI = 200
CHART_FONT_SIZE = 9
CHART_PASS_COLOR = "#" + COLORS["osdagGreen"]
CHART_FAIL_COLOR = "#" + COLORS["failRed"]
CHART_THRESHOLD_COLOR = "red"
CHART_THRESHOLD_STYLE = "--"
CHART_WIDTH_IN = 6.3           # about the text width at 100 %
CHART_UR_HEIGHT_IN = 5.2
CHART_MATERIAL_HEIGHT_IN = 3.0
CHART_STEEL_COLOR = "#4F6D7A"
CHART_CONCRETE_COLOR = "#9E9E9E"
CHART_REBAR_COLOR = "#B5651D"
CHART_FIG_WIDTH_LATEX = r"0.95\textwidth"


# ---------------------------------------------------------------------------
# Helpers that turn the settings above into LaTeX
# ---------------------------------------------------------------------------
def latex_colors():
    """\\definecolor lines for every entry of COLORS."""
    return "\n".join(
        r"\definecolor{%s}{HTML}{%s}" % (name, hexv) for name, hexv in COLORS.items()
    )


def latex_table_settings():
    """Table-related length / counter settings for the preamble."""
    return "\n".join([
        r"\setlength{\tabcolsep}{%gpt}" % TAB_COL_SEP_PT,
        r"\renewcommand{\arraystretch}{%g}" % ARRAY_STRETCH,
        r"\setlength{\LTpre}{%gpt}" % LT_PRE_PT,
        r"\setlength{\LTpost}{%gpt}" % LT_POST_PT,
        # longtable can only keep rows together within one chunk (default 20).
        r"\setcounter{LTchunksize}{%d}" % LT_CHUNK_SIZE,
        r"\setlength{\arrayrulewidth}{%gpt}" % ARRAY_RULE_WIDTH_PT,
        r"\setlength{\extrarowheight}{%gpt}" % EXTRA_ROW_HEIGHT_PT,
        # Only floating tables get \needspace. Doing it for longtable too makes
        # LaTeX leave half-empty pages and print a header-only row at the top of
        # the next page, because longtable already manages its own page breaks.
        r"\BeforeBeginEnvironment{table}{\needspace{%d\baselineskip}}" % NEEDSPACE_BASELINES,
    ])


def latex_geometry():
    return (
        r"\usepackage[%s, left=%s, right=%s, top=%s, bottom=%s, footskip=%dpt]{geometry}"
        % (PAPER, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, BOTTOM_MARGIN, FOOTSKIP_PT)
    )


def latex_headerfooter_style(name, project, job, date, rev, with_header=True):
    """LaTeX for one fancypagestyle with the standard Osdag header and footer."""
    if with_header:
        header = (
            r"  \fancyhead[L]{" + project + " $|$ " + job + "}\n"
            r"  \fancyhead[R]{" + date + " $|$ " + rev + "}\n"
            r"  \renewcommand{\headrule}{\color{osdagGreen}"
            r"\hrule width\headwidth height 1pt \vspace{2pt}}" "\n"
        )
    else:
        header = r"  \renewcommand{\headrulewidth}{0pt}" "\n"
    return _style_block(name, header, with_header)



def _style_block(name, header, with_header):
    footrule_core = (
        "  \\renewcommand{\\footrule}{%\n"
        "    \\ifbool{hasSDonPage}{%\n"
        "      \\vspace{-20pt}%\n"
        "      \\hbox to \\headwidth{\\textcolor{black}{\\footnotesize\\textit{* Software default value}}\\hfil}%\n"
        "      \\vspace{4pt}%\n"
        "    }{%\n"
        "      \\vspace{-8pt}%\n"
        "    }%\n"
        "    \\color{osdagGreen}\\hrule width\\headwidth height 1pt \\vspace{6pt}%\n"
        "  }\n"
    )
    if not with_header:
        footrule_core = (
            "  \\renewcommand{\\footrule}{\\vspace{-8pt}\\color{osdagGreen}"
            "\\hrule width\\headwidth height 1pt \\vspace{6pt}}\n"
        )
    return (
        "\\fancypagestyle{" + name + "}{\n  \\fancyhf{}\n" + header
        + "  \\fancyfoot[L]{" + FOOTER_LEFT + "}\n"
        + "  \\fancyfoot[R]{" + FOOTER_RIGHT + "}\n"
        + footrule_core + "}\n"
    )
