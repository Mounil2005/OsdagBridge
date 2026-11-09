"""
Table helpers for the OsdagBridge report.

Two post-processing passes are applied to the assembled LaTeX by
``postprocess_tables``:

1. ``add_repeating_headers``  - every ``longtable`` that has the usual shape::

       \\begin{longtable}{spec}
       \\caption{...}            (optional, may end in \\\\)
       \\hline
       <header row> \\\\
       \\hline

   gets ``\\endfirsthead`` after that block, followed by the header row again
   and ``\\endhead``, so the column headers repeat on every continued page.
   The caption is kept only in the first head, so table numbers and the list
   of tables are not duplicated and caption/heading order is preserved.

2. ``fit_column_widths`` - fixed ``p{..cm}`` / ``L{..cm}`` / ``C{..cm}`` /
   ``R{..cm}`` columns whose total width (plus column padding and rules) is
   larger than the text width are scaled down proportionally. This stops tables
   from running into the margins or footer.

Both passes are driven by values in ``theme`` and are no-ops on tables that
are already correct (e.g. tables that define ``\\endhead`` themselves).
"""

import re

from osdagbridge.core.reports import theme

_COL_RE = re.compile(r"(?P<kind>[LCRp])\{(?P<w>\d+(?:\.\d+)?)cm\}")
_BEGIN_RE = re.compile(r"^\\begin\{longtable\}\{(?P<spec>.*)\}\s*$")
_HEADER_END_RE = re.compile(r"\\\\(\[[^\]]*\])?\s*$")
_PT_PER_CM = 28.4528


def _spec_width_cm(spec):
    """Total rendered width of a column spec in cm (columns + padding + rules)."""
    widths = [float(m.group("w")) for m in _COL_RE.finditer(spec)]
    ncols = len(widths)
    if ncols == 0:
        return 0.0, 0
    n_rules = spec.count("|")
    pad_cm = ncols * 2 * theme.TAB_COL_SEP_PT / _PT_PER_CM
    rule_cm = n_rules * theme.ARRAY_RULE_WIDTH_PT / _PT_PER_CM
    return sum(widths) + pad_cm + rule_cm, ncols


def fit_column_widths(spec, max_cm=None):
    """Scale fixed-width columns of ``spec`` so the table fits ``max_cm``."""
    max_cm = max_cm or theme.TEXT_WIDTH_CM
    total, ncols = _spec_width_cm(spec)
    if ncols == 0 or total <= max_cm:
        return spec
    widths = [float(m.group("w")) for m in _COL_RE.finditer(spec)]
    fixed = total - sum(widths)           # padding + rules do not scale
    scale = max(0.3, (max_cm - fixed) / sum(widths))

    def repl(m):
        return "%s{%.2fcm}" % (m.group("kind"), float(m.group("w")) * scale)

    return _COL_RE.sub(repl, spec)


# Column spec of a longtable, possibly spread over several lines and containing
# one level of nested braces such as ``p{3cm}`` or ``>{\centering}p{3cm}``.
_SPEC_RE = re.compile(r"\\begin\{longtable\}\{((?:[^{}]|\{[^{}]*\})*)\}")


def fit_longtable_specs(tex, max_cm=None):
    """Apply ``fit_column_widths`` to every longtable column spec."""
    def repl(m):
        return "\\begin{longtable}{" + fit_column_widths(m.group(1), max_cm) + "}"
    return _SPEC_RE.sub(repl, tex)


def fix_caption_breaks(tex):
    """A ``\\caption`` inside a longtable must end with ``\\\\``.

    Without it LaTeX reports "Misplaced \\noalign" for the following rule.
    Only a caption on the line right after ``\\begin{longtable}`` is touched.
    """
    lines = tex.split("\n")
    for idx in range(len(lines) - 1):
        if _BEGIN_RE.match(lines[idx]):
            nxt = lines[idx + 1]
            if nxt.lstrip().startswith("\\caption") and not nxt.rstrip().endswith("\\\\"):
                lines[idx + 1] = nxt.rstrip() + "\\\\"
    return "\n".join(lines)


def add_repeating_headers(tex):
    """Insert \\endfirsthead / \\endhead so header rows repeat across pages."""
    lines = tex.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        out.append(line)
        if not _BEGIN_RE.match(line):
            i += 1
            continue

        # Locate the end of this table and skip it if it already manages headers.
        j = i + 1
        while j < n and not lines[j].startswith("\\end{longtable}"):
            j += 1
        body_head = "\n".join(lines[i + 1:min(j, i + 14)])
        if "\\endhead" in body_head or "\\endfirsthead" in body_head:
            i += 1
            continue

        # Expected: optional caption line(s), \hline, header row, \hline
        k = i + 1
        pre = []
        while k < j and not lines[k].strip().startswith("\\hline"):
            if lines[k].strip().startswith("\\caption") or not lines[k].strip():
                pre.append(lines[k])
                k += 1
            else:
                break
        if (k + 2 < j and lines[k].strip() == "\\hline"
                and _HEADER_END_RE.search(lines[k + 1])
                and "&" in lines[k + 1]
                and lines[k + 2].strip() == "\\hline"):
            header = lines[k + 1]
            # a caption must end with \\ before \hline inside a longtable
            for p in pre:
                if p.strip().startswith("\\caption") and not p.rstrip().endswith("\\\\"):
                    p = p.rstrip() + "\\\\"
                out.append(p)
            out.extend([lines[k], header, lines[k + 2], "\\endfirsthead",
                        lines[k], header, lines[k + 2], "\\endhead"])
            i = k + 3
            continue
        i += 1
    return "\n".join(out)


_ROW_END_RE = re.compile(r"\\\\(?P<star>\*)?(?P<opt>\[[^\]]*\])?\s*$")
_MULTIROW_RE = re.compile(r"^\s*\\multirow\{(?P<n>\d+)\}")


def _no_break_after(line):
    """Return ``line`` with its row terminator changed to the no-page-break ``\\\\*``."""
    m = _ROW_END_RE.search(line)
    if not m or m.group("star"):
        return line
    return line[:m.start()] + "\\\\*" + (m.group("opt") or "")


def keep_rows_together(tex):
    """Stop page breaks that split a multirow group or orphan a closing rule.

    * Rows that belong to one ``\\multirow{N}{*}`` group (e.g. all checks of one
      girder) are tied together with ``\\\\*`` so the group is not cut by a page
      break.
    * The last data row of a longtable is tied to the closing ``\\hline`` so a
      break cannot leave a lone rule (and a repeated header) on the next page.
    """
    lines = tex.split("\n")
    in_table = False
    pending = 0                      # rows still to tie inside a multirow group
    last_row_idx = None
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("\\begin{longtable}"):
            in_table, pending, last_row_idx = True, 0, None
            continue
        if not in_table:
            continue
        if s.startswith("\\end{longtable}"):
            if last_row_idx is not None:
                lines[last_row_idx] = _no_break_after(lines[last_row_idx])
            in_table = False
            continue
        is_row_end = bool(_ROW_END_RE.search(line)) and "\\hline" not in s[:6]
        m = _MULTIROW_RE.match(line)
        if m:
            pending = int(m.group("n"))
        if is_row_end and "&" in line:
            last_row_idx = idx
            if pending > 1:
                lines[idx] = _no_break_after(line)
            if pending > 0:
                pending -= 1
    return "\n".join(lines)


def postprocess_tables(tex):
    """Apply all table post-processing passes configured in ``theme``."""
    tex = fix_caption_breaks(tex)
    if theme.FIT_TABLES_TO_PAGE:
        tex = fit_longtable_specs(tex)
    if theme.REPEAT_TABLE_HEADERS:
        tex = add_repeating_headers(tex)
    tex = keep_rows_together(tex)
    return tex
