"""Unit tests for the report table post-processing and chart helpers."""
import os

from osdagbridge.core.reports import theme
from osdagbridge.core.reports.tables import (
    add_repeating_headers,
    fit_column_widths,
    fix_caption_breaks,
    keep_rows_together,
    postprocess_tables,
)
from osdagbridge.core.reports import charts

TABLE = "\n".join([
    r"\begin{longtable}{|L{5.5cm}|p{10.0cm}|}",
    r"\caption{\textbf{Demo}}",
    r"\hline",
    r"\textbf{parameter} & \textbf{value} \\",
    r"\hline",
    r"a & 1 \\[6pt]",
    r"\hline",
    r"b & 2 \\[6pt]",
    r"\hline",
    r"\end{longtable}",
])


def test_repeating_header_is_inserted_once():
    out = add_repeating_headers(fix_caption_breaks(TABLE))
    assert out.count(r"\endfirsthead") == 1
    assert out.count(r"\endhead") == 1
    # caption stays in the first head only
    assert out.count(r"\caption") == 1
    assert out.index(r"\caption") < out.index(r"\endfirsthead") < out.index(r"\endhead")


def test_caption_gets_line_break():
    assert r"\caption{\textbf{Demo}}\\" in fix_caption_breaks(TABLE)


def test_tables_with_own_header_handling_are_untouched():
    own = TABLE.replace(r"\hline" + "\n" + r"a &", r"\endhead" + "\n" + r"a &", 1)
    assert add_repeating_headers(own).count(r"\endfirsthead") == 0


def test_wide_spec_is_scaled_to_text_width():
    spec = "|L{5.5cm}|p{10.0cm}|"
    fitted = fit_column_widths(spec)
    import re
    widths = [float(w) for w in re.findall(r"\{([\d.]+)cm\}", fitted)]
    assert sum(widths) < sum([5.5, 10.0])
    assert fit_column_widths("|L{3cm}|p{4cm}|") == "|L{3cm}|p{4cm}|"   # already fits


def test_multiline_spec_is_scaled():
    from osdagbridge.core.reports.tables import fit_longtable_specs
    t = ("\\begin{longtable}{|C{2.5cm}|C{3.5cm}|\n"
         ">{\\centering\\arraybackslash}p{4.2cm}|C{3.5cm}|C{2.5cm}|}\n\\hline\n\\end{longtable}")
    out = fit_longtable_specs(t)
    import re
    assert sum(float(w) for w in re.findall(r"\{([\d.]+)cm\}", out)) < 16.2
    assert "\\centering\\arraybackslash" in out


def test_last_row_is_tied_to_closing_rule():
    out = keep_rows_together(TABLE)
    assert r"b & 2 \\*[6pt]" in out
    assert r"a & 1 \\[6pt]" in out


def test_multirow_group_is_tied_together():
    t = "\n".join([
        r"\begin{longtable}{|C{2cm}|C{3cm}|}",
        r"\multirow{2}{*}{G1} & x \\[6pt]",
        r"\cline{2-2}",
        r" & y \\[6pt]",
        r"\hline",
        r"\multirow{2}{*}{G2} & x \\[6pt]",
        r" & y \\[6pt]",
        r"\end{longtable}",
    ])
    out = keep_rows_together(t)
    assert r"{G1} & x \\*[6pt]" in out      # first row of a group is tied
    assert r"{G2} & x \\*[6pt]" in out


def test_postprocess_is_idempotent_enough():
    once = postprocess_tables(TABLE)
    assert once.count(r"\endhead") == 1
    assert postprocess_tables(once).count(r"\endhead") == 1


def test_theme_values_are_consistent():
    assert theme.TEXT_WIDTH_CM > 15
    assert theme.UR_THRESHOLD == 1.0
    assert "osdagGreen" in theme.latex_colors()


def test_ur_chart_writes_png_and_returns_latex(tmp_path):
    records = [("Girder --- Moment", 0.2), ("Girder --- Fatigue", 1.58),
               ("Deck --- Punching Shear", 0.34), ("Cross Bracing --- Tension", 0.21),
               ("End Diaphragm --- Shear", 0.21), ("Crack Width (slab)", None)]
    tex = charts.ur_chart(records, str(tmp_path))
    assert r"\includegraphics" in tex
    assert os.path.exists(tmp_path / "ur_summary_chart.png")


def test_material_chart_handles_missing_values(tmp_path):
    q = {"steel_girders_wt_total": "32.89", "bracing_top_wt_total": "0.11",
         "bracing_bot_wt_total": "0.11", "bracing_diag_wt_total": "0.25",
         "concrete_deck_vol_total": "63.00", "rebar_deck_wt_total": "N.A."}
    assert r"\includegraphics" in charts.material_chart(q, str(tmp_path))
    assert charts.material_chart({}, str(tmp_path)) == ""


def test_unicode_math_symbols_are_escaped():
    from osdagbridge.core.reports.report_utils import _tex
    assert r"$\leq$" in _tex("Leg ≤ H")


def test_end_diaphragm_steel_quantity():
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    pre = "member_properties.end_diaphragm_details."
    outputs = {"crossbracing_forces_dict": {"geometry": {"girder_depth_m": 1.67}}}
    for p in (1, 2, 3):
        s = f"G{p}G{p + 1}.E{p}M1"
        outputs.update({
            f"{pre}section_properties.area.{s}": 19.1,       # cm2
            f"{pre}type.{s}": "Cross Bracing",
            f"{pre}bracing_type.{s}": "X-Bracing",
            f"{pre}top_chord.{s}": "Yes",
            f"{pre}bottom_chord.{s}": "Yes",
        })
    inputs = {"geometry.span": "30", "typical_section.no_of_girders": "4",
              "typical_section.girder_spacing": "2.1"}
    q = calculate_material_quantities(inputs, outputs)
    # 3 panels x 2 supports x (2 diagonals + top + bottom chord) = 24 members
    assert q["end_diaphragm_qty"] == "24"
    # 6 diaphragms x (2 x hypot(2.1, 1.67) + 2 x 2.1) = 57.40 m, area 19.1 cm2, 7.85 t/m3
    assert abs(float(q["end_diaphragm_wt_total"]) - 0.86) < 0.01


def test_material_chart_includes_end_diaphragm_and_shared_axis(tmp_path):
    q = {"steel_girders_wt_total": "32.89", "bracing_top_wt_total": "0.11",
         "bracing_bot_wt_total": "0.11", "bracing_diag_wt_total": "0.25",
         "end_diaphragm_wt_total": "0.86",
         "concrete_deck_vol_total": "63.00", "rebar_deck_wt_total": "7.56"}
    tex = charts.material_chart(q, str(tmp_path))
    assert "not quantified separately" not in tex
    assert os.path.exists(tmp_path / "material_quantities_chart.png")
