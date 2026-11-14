# OsdagBridge Report Generator: Technical Changes

Branch: `task-latex-report` (from `dev`). All changes are under `src/osdagbridge/core/reports/`.
Before/after PDFs: `before/Report_Before.pdf`, `after/Report_After.pdf`, both produced headlessly from the same
`testing/osi_files/TC-baseline_inputs.osi` (span 30 m, carriageway 7.5 m, defaults), using
`examples/generate_report_headless.py`. `before/Report_Before_GUI.pdf` is the same design generated from the GUI.

## 1. Summary by requirement

| # | Requirement | What was wrong | Fix |
|---|---|---|---|
| 1 | Repeat table headers across pages | All 49 tables were `longtable`s, but only 2 defined `\endhead`. The other 47 lost their header on page 2+. | `tables.add_repeating_headers()` inserts `\endfirsthead` and `\endhead` (header row repeated). The caption stays in the first head only, so numbering and the list of tables are not duplicated. 48 of 49 tables fixed; the remaining one already had its own. |
| 2 | Footer overlap / vertical spacing | Text block ran to the footer; tables 17.6 cm wide on a 15.9 cm text block; `\needspace` on every longtable left half-empty pages and a header-only orphan row. | Bottom margin and `footskip` set in `theme.py`; `tables.fit_column_widths()` scales fixed-width columns to the text width; `\needspace` kept for floats only; `keep_rows_together()` ties multirow groups (one girder = one block) and the last row to the closing rule with `\\*`; `LTchunksize` raised so ties work across 20-row chunks; `\raggedbottom`. |
| 3 | Load tables (Chapter 3) | Vehicles, impact, braking and footpath load were merged in one 2-column table; footpath value was blank because the computed `fp_str` was never used. | Split into Table 3.3 Vehicular live loads (one row per vehicle selected in the Loading tab, with type, impact factor and IRC 6 clause), Table 3.4 Braking and centrifugal loads, Table 3.5 Footpath live load; all with Value / Unit / Reference columns. Also: Vz and Pz now use the values the code already computed (`vz_str`, `pz_str`). |
| 4 | UR charts (Section 5.5) | Table only. | `charts.ur_chart()`: 2x2 bar charts (Steel Plate Girders, Concrete Deck Slab, Cross Bracing, End Diaphragms), red dashed line at UR = `theme.UR_THRESHOLD` (1.0), failing bars in red. URs are collected from the same rows that build Table 5.29, so chart and table cannot disagree. Embedded as Figure 5.1. |
| 5 | Material charts (Chapter 7) | Table only; the bill of materials had no End Diaphragm steel quantity. | `boq_generator.py` now computes End Diaphragm steel (new Table 7.1 row 2(d): 2 diaphragms per panel, diagonals and chords or a single beam, member area from `member_properties.end_diaphragm_details.section_properties.area`). `charts.material_chart()` shows steel tonnage (girders, cross bracing, end diaphragms) and deck concrete volume vs reinforcement weight on **one shared axis**, as the Osdag mentors asked. Embedded as Figure 7.1. |
| 6 | Centralized style | Page geometry, colours, table paddings and header/footer hard-coded in `report_generator.py`. | `theme.py` is the single source of truth (see section 3). `report_generator.preamble()` builds geometry, colours, table settings and the three fancyhdr styles from it. |

## 2. Files changed

| File | Change |
|---|---|
| `theme.py` (new) | Central style configuration and LaTeX snippet helpers |
| `tables.py` (new) | Post-processing of longtables (headers, widths, row ties, caption breaks) |
| `charts.py` (new) | UR and material bar charts (matplotlib, Agg backend, never raises) |
| `report_generator.py` | Imports theme; preamble built from theme; `postprocess_tables()` applied to the assembled document; charts get a temp image directory |
| `chap3.py` | Live-load tables split; Vz/Pz fixed |
| `chap5.py` | Collects UR values in `_row522`; embeds UR chart in Section 5.5 (`asset_dir` parameter) |
| `chap7.py` | Embeds material chart (`asset_dir` parameter); new Table 7.1 row 2(d) End Diaphragm |
| `core/boq/boq_generator.py` | End Diaphragm steel quantity (`end_diaphragm_*` keys) |
| `report_utils.py` | `_tex()` now converts Unicode math symbols (`≤ ≥ ± σ λ ...`) |
| `examples/generate_report_headless.py` (new) | Headless design + report run for before/after comparison |
| `tests/unit/test_report_tables.py` (new) | 14 unit tests for table passes, charts, `_tex`, End Diaphragm quantity |

## 3. Structure of `theme.py`
- **Page:** `PAGE_MARGIN`, `BOTTOM_MARGIN`, `FOOTSKIP_PT`, `LINE_STRETCH`, `TEXT_WIDTH_CM`
- **Colours:** `COLORS` dict (`osdagGreen`, `headerFill`, `failRed`, ...) emitted by `latex_colors()`
- **Tables:** `TAB_COL_SEP_PT`, `ARRAY_STRETCH`, rule width, `LT_CHUNK_SIZE`, switches `REPEAT_TABLE_HEADERS`, `FIT_TABLES_TO_PAGE`; emitted by `latex_table_settings()`
- **Header/footer:** `FOOTER_LEFT/RIGHT`, `latex_headerfooter_style()` for the `main`, `plain` and `firstpage` styles
- **Charts:** `UR_THRESHOLD`, fonts, DPI, sizes, bar and threshold colours

Chapter generators and `report_generator.py` import values from this module and no longer hold their own.

## 4. Design decisions
- **Post-processing instead of editing 49 tables by hand.** The tables share one shape (caption, `\hline`, header, `\hline`), so one tested pass fixes all of them and any table added later. Existing tables that define `\endhead` themselves are skipped. The previous code comment warned that an automatic pass could mis-order captions and headings; this pass keeps the caption in the first head and was checked on every table.
- **Removing `\needspace` for longtable.** It fights longtable's own output routine. With it, a header-only row was printed at the top of the next page and pages were left half empty.
- **Charts never break the report.** `charts.py` catches exceptions and returns an empty string.
- **UR threshold = 1.0** (UR = Demand / Capacity, as in the report notes), confirmed by the Osdag mentors on Discord; it lives in one constant (`theme.UR_THRESHOLD`).
- **End diaphragm steel quantity** added to the bill of materials on the mentors' request. Count and length per diaphragm: X-bracing = 2 diagonals of length sqrt(spacing^2 + girder depth^2) plus top and bottom chords of length spacing when enabled; beam type = one member of length spacing; two diaphragms per panel (one per support). Weight = area x length x 7.85 t/m3, the same convention as the cross bracing rows.
- **Concrete volume and reinforcement weight share one axis** (mentors' instruction); each bar is labelled with its own unit.

## 5. Results (same inputs)
| Item | Before | After |
|---|---|---|
| `Misplaced \noalign` / `\omit` / `Extra alignment tab` errors (pdflatex log) | 46 / 46 / 46 | 0 / 0 / 0 |
| `Unicode character ≤ not set up` errors | 1 | 0 |
| Overfull hboxes of 20 pt or more | 30 | 6 |
| Tables with repeated header | 2 of 49 | 49 of 49 |
| Pages | 51 | 54 (two figures added, tables take more room once they fit) |

Measured by compiling `Report_Before.tex` and `Report_After.tex` with pdflatex (MiKTeX 25.12) and counting log entries.
The 6 remaining overfull boxes are paragraphs (long unbreakable strings) and one figure placeholder that only exists
in headless mode; none are tables.
| UR chart / material chart | none | Figure 5.1 / Figure 7.1 |

## 6. Known limitations
- End diaphragm member area is taken as stored in the section properties; if that value is for a single angle of a double-angle section, the End Diaphragm steel is understated by up to a factor of two.
- Headless mode renders no CAD figures; figure slots show placeholders. Generate the final `Report_After.pdf` from the GUI for the submission.
- Multirow groups taller than a page can still split.
