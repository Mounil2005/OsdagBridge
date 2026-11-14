"""
Matplotlib charts embedded in the OsdagBridge report.

* ``ur_chart``       - utilization-ratio bar charts per component (Section 5.5)
* ``material_chart`` - material quantity bar charts (Chapter 7)

Both functions write a PNG into ``out_dir`` and return the LaTeX that embeds
it (or an empty string when there is nothing to plot), so a chart problem can
never break report generation. All styling comes from ``theme``.
"""

import logging
import os
import re

from osdagbridge.core.reports import theme

_log = logging.getLogger(__name__)

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

# Component groups of the UR charts: (title, label-prefix tests)
UR_GROUPS = [
    ("Steel Plate Girders", ("Girder",)),
    ("Concrete Deck Slab", ("Deck", "Transverse Shear (slab)", "Crack Width (slab)")),
    ("Cross Bracing", ("Cross Bracing",)),
    ("End Diaphragms", ("End Diaphragm",)),
]


def to_float(value):
    """First number found in a string / number, else None ('N.A.', '---', '')."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = _NUM_RE.search(str(value))
    return float(m.group(0)) if m else None


def _plt():
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": theme.CHART_FONT_SIZE})
    return plt


def _short_label(label):
    for prefix in ("Girder --- ", "Deck --- ", "Cross Bracing --- ", "End Diaphragm --- "):
        if label.startswith(prefix):
            return label[len(prefix):]
    return label.replace(" (slab)", "")


def _embed(rel_path, caption):
    return (
        "\n\\begin{figure}[H]\n\\centering\n"
        "\\includegraphics[width=" + theme.CHART_FIG_WIDTH_LATEX + "]{" + rel_path + "}\n"
        "\\caption{" + caption + "}\n\\end{figure}\n"
    )


def ur_chart(records, out_dir, rel_dir="images"):
    """Bar charts of UR (Demand/Capacity) per component group.

    ``records``: iterable of (label, ur_float). Returns LaTeX or ''.
    """
    try:
        groups = []
        for title, prefixes in UR_GROUPS:
            items = [(_short_label(l), u) for l, u in records
                     if u is not None and any(l.startswith(p) for p in prefixes)]
            if items:
                groups.append((title, items))
        if not groups:
            return ""
        plt = _plt()
        n = len(groups)
        ncols = 2 if n > 1 else 1
        nrows = (n + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, squeeze=False,
                                 figsize=(theme.CHART_WIDTH_IN, theme.CHART_UR_HEIGHT_IN))
        thr = theme.UR_THRESHOLD
        for ax in axes.flat[n:]:
            ax.axis("off")
        for ax, (title, items) in zip(axes.flat, groups):
            labels = [l for l, _ in items]
            vals = [u for _, u in items]
            colors = [theme.CHART_FAIL_COLOR if v > thr else theme.CHART_PASS_COLOR for v in vals]
            ax.bar(range(len(vals)), vals, color=colors, width=0.65)
            ax.axhline(thr, color=theme.CHART_THRESHOLD_COLOR,
                       linestyle=theme.CHART_THRESHOLD_STYLE, linewidth=1.2)
            ax.set_xticks(range(len(vals)))
            ax.set_xticklabels([_wrap(l) for l in labels], rotation=45, ha="right", fontsize=7)
            ax.set_ylim(0, max(thr * 1.2, max(vals) * 1.18))
            ax.set_ylabel("Utilization Ratio")
            ax.set_title(title, fontsize=theme.CHART_FONT_SIZE + 1, fontweight="bold")
            for i, v in enumerate(vals):
                ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=7)
            ax.spines[["top", "right"]].set_visible(False)
        fig.legend(
            handles=[plt.Line2D([0], [0], color=theme.CHART_THRESHOLD_COLOR,
                                linestyle=theme.CHART_THRESHOLD_STYLE,
                                label=f"Limit (UR = {thr:g})")],
            loc="lower center", frameon=False, ncol=1)
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        os.makedirs(out_dir, exist_ok=True)
        fname = "ur_summary_chart.png"
        fig.savefig(os.path.join(out_dir, fname), dpi=theme.CHART_DPI)
        plt.close(fig)
        return _embed(rel_dir + "/" + fname,
                      "Utilization Ratio (Demand / Capacity) of the governing checks. "
                      "Bars above the red dashed line fail.")
    except Exception as exc:  # never let a chart break the report
        _log.warning("UR chart skipped: %s", exc)
        return ""


def _wrap(text, width=14):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def material_chart(q, out_dir, rel_dir="images"):
    """Two bar charts: steel tonnage by member group, concrete volume vs rebar weight.

    ``q`` is the quantities dict from ``calculate_material_quantities``.
    Returns LaTeX or ''.
    """
    try:
        girders = to_float(q.get("steel_girders_wt_total"))
        bracing_parts = [to_float(q.get(k)) for k in
                         ("bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total")]
        bracing = sum(p for p in bracing_parts if p is not None) if any(
            p is not None for p in bracing_parts) else None
        diaphragm = to_float(q.get("end_diaphragm_wt_total"))
        concrete_vol = to_float(q.get("concrete_deck_vol_total"))
        rebar_wt = to_float(q.get("rebar_deck_wt_total"))

        steel = [("Girders", girders), ("Cross Bracing", bracing), ("End Diaphragms", diaphragm)]
        steel = [(l, v) for l, v in steel if v is not None]
        if not steel and concrete_vol is None and rebar_wt is None:
            return ""

        plt = _plt()
        fig, (ax1, ax2) = plt.subplots(
            1, 2, figsize=(theme.CHART_WIDTH_IN, theme.CHART_MATERIAL_HEIGHT_IN),
            gridspec_kw={"width_ratios": [1.5, 1]})
        title_kw = dict(fontsize=theme.CHART_FONT_SIZE + 1, fontweight="bold")

        if steel:
            vals = [v for _, v in steel]
            ax1.bar([_wrap(l, 10) for l, _ in steel], vals, color=theme.CHART_STEEL_COLOR, width=0.6)
            for i, v in enumerate(vals):
                ax1.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
            ax1.set_ylim(0, max(vals) * 1.2 if max(vals) > 0 else 1)
        ax1.set_ylabel("Structural steel (MT)")
        ax1.set_title("Steel Tonnage", **title_kw)
        ax1.tick_params(axis="x", labelsize=8)

        # Concrete volume (m3) and reinforcement weight (MT) are drawn on one shared
        # axis, as requested by the Osdag mentors; each bar is labelled with its unit.
        pair = [("Deck concrete\n(m$^3$)", concrete_vol, theme.CHART_CONCRETE_COLOR),
                ("Reinforcement\n(MT)", rebar_wt, theme.CHART_REBAR_COLOR)]
        vals2 = [v or 0 for _, v, _ in pair]
        ax2.bar(range(2), vals2, color=[c for _, _, c in pair], width=0.55)
        ax2.set_xticks(range(2))
        ax2.set_xticklabels([l for l, _, _ in pair], fontsize=8)
        ax2.set_ylabel("Quantity (m$^3$ or MT)")
        ax2.set_title("Concrete vs Reinforcement", **title_kw)
        for i, v in enumerate(vals2):
            if v:
                ax2.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
        if max(vals2) > 0:
            ax2.set_ylim(0, max(vals2) * 1.2)
        for ax in (ax1, ax2):
            ax.spines[["top", "right"]].set_visible(False)

        fig.tight_layout()
        os.makedirs(out_dir, exist_ok=True)
        fname = "material_quantities_chart.png"
        fig.savefig(os.path.join(out_dir, fname), dpi=theme.CHART_DPI)
        plt.close(fig)
        note = "Material quantities from Table 7.1."
        if diaphragm is None:
            note += " End-diaphragm steel is not quantified separately in the bill of materials."
        return _embed(rel_dir + "/" + fname, note)
    except Exception as exc:
        _log.warning("Material chart skipped: %s", exc)
        return ""
